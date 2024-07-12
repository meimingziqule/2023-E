import sensor, image, time, pyb,math,lcd
from pyb import UART, LED,Pin, Timer
# 50kHz pin6 timer2 channel1
#light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
#light.pulse_width_percent(50) # 控制亮度 0~100
#11
red_thresholds = (0, 100, 11, 91, -20, 54)# 通用红色阈值
green_thresholds = (0, 100, 5, 127, -61, 122)# 通用绿色阈值   待修改
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.SVGA)   # Set frame size tov SVGA(800x600)
sensor.set_windowing([370,176,335,335]) #roi 300,0,200,600
sensor.set_hmirror(True)
sensor.set_vflip(True)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_contrast(2)
sensor.set_gainceiling(8)
#sensor.set_auto_exposure(False,35000)#设置感光度  这里至关重要
still_send_flag = 0
clock = time.clock()
red_blobs = 0
lcd.init(freq=15000000)
uart = UART(3,115200)
uart.init(115200, bits=8, parity=None, stop=1 )
black_blob = None
black_thresholds = (0, 15, -5, 82, 1, 126)
black_roi = None
get_black_roi_flag = 1

start_flag = 1
line_num  = 0
one_error_x = 0
one_error_y = 0
error_x = 0
error_y = 0

task_flag = 0
red_blob = None
i=0
rect_flag  = 1
rect_points = []
rect_points_flag = 1
send_data = None

buffer = None

data = ''
data_decoded  = 0
rect_point_num = 0
frame_head = '#'
frame_tail = ';'
first_recieve_flag = 1

l_value= 60
baoguang = 30000
baoguang_step = 1500
sensor.set_auto_exposure(False,baoguang)#设置感光度  这里至关重要
auto_exposure_flag = True
auto_exposure_first = True

rect_points_transform = None

def remove_duplicates_preserve_order(input_list):
    """
    去除列表中的重复元素，并返回一个去重后的列表，保留原始顺序。

    参数:
    input_list (list): 输入的列表，可能包含重复元素。

    返回:
    list: 去重后的列表，保留原始顺序。
    """
    seen = set()
    unique_list = []
    for item in input_list:
        if item not in seen:
            seen.add(item)
            unique_list.append(item)
    return unique_list


def scale_rect_points(rect_points, scale_factor):
    """
    将矩形框上的坐标点列表按给定的比例因子进行缩放，并保持矩形的中心点不变。

    参数:
    rect_points (list): 包含矩形框上坐标点的列表，例如[(x1, y1), (x2, y2), ..., (xn, yn)]
    scale_factor (float): 缩放比例因子

    返回:
    list: 包含缩放后坐标点的列表，例如[(x1', y1'), (x2', y2'), ..., (xn', yn')]
    """
    # 计算矩形的中心点
    x_coords = [point[0] for point in rect_points]
    y_coords = [point[1] for point in rect_points]
    center_x = sum(x_coords) / len(rect_points)
    center_y = sum(y_coords) / len(rect_points)

    # 缩放后的坐标点
    scaled_points = []
    for point in rect_points:
        x = center_x + (point[0] - center_x) / scale_factor
        y = center_y + (point[1] - center_y) / scale_factor
        # 保留一位小数
        x = round(x, 1)
        y = round(y, 1)
        scaled_points.append((x, y))

    return scaled_points

#线段分割函数
def divide_line_segment(point1, point2, n):
    """
    将两个点连成的线段平分成n份，并返回包含这些点的数组。

    参数:
    point1 (tuple): 第一个点的坐标 (x1, y1)
    point2 (tuple): 第二个点的坐标 (x2, y2)
    n (int): 要平分的份数

    返回:
    list: 包含所有点的数组，例如[(x1, y1), (x2, y2), ...]CC
    """
    if n < 1:
        raise ValueError("n必须大于等于1")

    x1, y1 = point1
    x2, y2 = point2

    points = []
    for i in range(n + 1):
        x = x1 + (x2 - x1) * i / n
        y = y1 + (y2 - y1) * i / n
        points.append((x, y))

    return points

#矩形分割函数
def divide_polygon_segments(points, n):
    """
    将一个四边形的每条边平分成n份，并将所有结果拼接成一个新的列表。

    参数:
    points (list): 包含四个点的列表，例如[(x1, y1), (x2, y2), (x3, y3), (x4, y4)]
    n (int): 要平分的份数

    返回:
    list: 包含所有点的数组，例如[(x1, y1), (x2, y2), ..., (x4, y4), ...]
    """
    if len(points) != 4:
        raise ValueError("points列表必须包含四个点")

    result = []
    for i in range(4):
        segment_points = divide_line_segment(points[i], points[(i + 1) % 4], n)
        result.extend(segment_points)

    return result

def find_rect_corners(rect,img):
    for r in rect:
        #img.draw_rectangle(r.rect(), color = (255, 0, 0))
        corners = change_condi(r.corners())
        for p in corners:  # 颠倒点的顺序
            img.draw_cross(p[0], p[1], 5, color = (0, 255, 0))
        print(corners)#打印顶点[(x1,y1),................]
    return corners
def find_max_red_blobs(blobs, img):
    if not blobs:
        print("没有找到任何 blobs")
        return None

    try:
        red_blob = max(blobs, key=lambda b: b.pixels())
        #print("x:%d,y:%d,w:%d,h:%d" % (red_blob.cx(), red_blob.cy(), red_blob.w(), red_blob.h()))
        img.draw_cross(red_blob.cx(),red_blob.cy())
        print("红色像素数量：%d" % red_blob.pixels())
        return red_blob
    except Exception as e:
        print("发生错误: ", e)
        return None

#使顶点数组顺时针
def change_condi(corners_list):
    corners = [0,0,0,0]
    corners[0] = corners_list[-1]
    corners[1] = corners_list[-2]
    corners[2] = corners_list[-3]
    corners[3] = corners_list[-4]
    if corners is not None:
        return corners
#计算误差
#求error_x error_y
def error_distance(corners,x,y):
    error_x = corners[0]-x
    error_y = corners[1]-y
    if abs(error_x) and abs(error_y):
        return error_x,error_y  ##？？？？
    else:
        return None,None
#运动路径选择与误差计算
def next_target_error(line_num,red_blobs,corners):
    one_error_x,one_error_y = error_distance(corners[line_num-1],red_blobs.cx(),red_blobs.cy())
    return one_error_x,one_error_y
#判断下一次该发送哪个顶点
def now_conditiont(blob, corners):
    for line_num, corner in enumerate(corners):
        if (abs(blob.cx() - corner[0]) < 5) and (abs(blob.cy() - corner[1]) < 5):#用于判断哪个顶点
            return line_num + 1
    return None  # 如果没有找到匹配的顶点，返回 None

def receive_data():
    global buffer
    buffer = buffer.lstrip('#')  # 去除缓冲区头部的多余'#'
    
    
    if uart.any():
        char = uart.read(1).decode()
        
        if char == '#':
            buffer = ""  # 清空缓冲区，准备接收新数据
        elif char == ';':
            if buffer:  # 确保有数据才返回
                data = buffer
                buffer = ""  # 清空缓冲区，准备接收下一个数据包
                return data
        else:
            buffer += char  # 将字符添加到缓冲区
        
    else:
        # 如果没有数据，可以适当等待，避免CPU空转
        time.sleep_ms(1)

def receive_data():
    global buffer
    buffer = buffer.lstrip('#')  # 去除缓冲区头部的多余'#'
    
    
    if uart.any():
        char = uart.read(1).decode()
        
        if char == '#':
            buffer = ""  # 清空缓冲区，准备接收新数据
        elif char == ';':
            if buffer:  # 确保有数据才返回
                data = buffer
                buffer = ""  # 清空缓冲区，准备接收下一个数据包
                return data
        else:
            buffer += char  # 将字符添加到缓冲区
        
    else:
        # 如果没有数据，可以适当等待，避免CPU空转
        time.sleep_ms(1)

buffer = ""  # 初始化全局变量用于存储数据

while True:
        # Take a picture and return the image.
    clock.tick()                    # Update the FPS clock.
    
    img = sensor.snapshot()         # Take a picture and return the image.
    red_blobs = img.find_blobs([red_thresholds],x_stride=1, y_stride=1, pixels_threshold=5)
    #识别色块
    if red_blobs:
        red_blob = find_max_red_blobs(red_blobs,img)
        print('找到了色块')
        print("red_blobs,X:%s,Y:%s"%(red_blob.cx(),red_blob.cy()))
        img.draw_rectangle(red_blob.rect(), color = (255, 255, 255))
    #识别黑色色块，获取roi区域
    if get_black_roi_flag == 1:
        black_blobs = img.find_blobs([black_thresholds],x_stride=100, y_stride=100, pixels_threshold=5000)
        if black_blobs:
            black_blob = find_max_red_blobs(black_blobs,img)#借用一下红色的函数
            print('找到了黑色色块')
            print("black_blobs,X:%s,Y:%s"%(black_blob.cx(),black_blob.cy()))
            
            black_roi= (black_blob.rect()[0]-5,black_blob.rect()[1]-5,black_blob.rect()[2]+10,black_blob.rect()[3]+10)
            img.draw_rectangle(black_roi, color = (255, 255, 255))
            if black_roi is not None:
                  get_black_roi_flag = 0
    #识别矩形
    if rect_flag ==1:
        rect = img.find_rects(threshold = 17000)
        if rect:
            corners = find_rect_corners(rect,img)#找顶点[(x1,y1),................]
            if corners:
                rect_flag =0 #矩形只识别一次
        else:
            print("没找到矩形")
    else:
        print("corner:",corners)
        img.draw_rectangle(rect[0].rect(), color = (255, 255, 255))
    print("rect_points_flag",rect_points_flag)

    #识别一次矩形
    if rect_points_flag == 1:
        if rect:
            rect_points = divide_polygon_segments(corners, 2)#如[(0.0, 0.0), (10.0, 1.2), (20.0, 2.4), (30.0, 3.6), (40.0, 4.8), (50.0, 6.0), (50.0, 6.0), (48.0, 10.8)]
            rect_points_transform =  scale_rect_points(rect_points,1.06)#缩放
            rect_points_transform = remove_duplicates_preserve_order(rect_points_transform)#去重
            #rect_points_transform[4]  =(rect_points_transform[4][0]-3,rect_points_transform[4][1]+7)
            rect_points_flag = 0 #只计算一次
            print("rect_point:",rect_points)
    #如果接收到了坐标发送信号且矩形识别完成
    print("rect_points",rect_points)
    print("rect_points_transform",rect_points_transform)
    histogram = img.histogram()
    histogram_statistics = histogram.get_statistics()
    #print(histogram_statistics)
    
    data = receive_data()

    if data=='B' and rect_points_flag == 0:
        still_send_flag = 1
        LED(3).on()
    elif data == 'A' and rect_points_flag == 0:
        rect_point_num += 1
        data = 'B'
        print("111312312222221122222222222222222222222222222222222222222222222222222222222222")
    else:
        #print('等待接收数据')
        pass
    
    if still_send_flag ==1:    #持续发送坐标
        print("still_send_flag",still_send_flag)
        if rect_points is not None and red_blobs is not None:
            if  rect_point_num<len(rect_points_transform):
                send_data = '#0'+'X'+str(rect_points_transform[rect_point_num][0])+'Y'+str(rect_points_transform[rect_point_num][1])+'x'+str(float(red_blob.cx()))+'y'+str(float(red_blob.cy()))+';'
                print(send_data)
                print('3333333333333333333333333333333333333333333333')
                uart.write(send_data)
            else:
                rect_point_num = 0
    if rect_points_transform is not None  :            
        img.draw_cross(int(rect_points_transform[rect_point_num][0]),int(rect_points_transform[rect_point_num][1]))            
    #print("一次任务结束")
    fps = 'fps:'+str(clock.fps())
    img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
    print(clock.fps())

#方案二 ： 当激光进入顶点范围直接发送前后顶点的error_x,error_y——————————>减少代码执行量，提高效率     