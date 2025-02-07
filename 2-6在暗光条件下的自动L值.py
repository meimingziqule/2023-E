import sensor, image, time, pyb,math,lcd
from pyb import UART, LED,Pin, Timer
# 50kHz pin6 timer2 channel1
#light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
#light.pulse_width_percent(50) # 控制亮度 0~100

red_thresholds = (0, 100, 8, 89, -3, 65)# 通用红色阈值
green_thresholds = (0, 100, 5, 127, -61, 122)# 通用绿色阈值   待修改
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.SVGA)   # Set frame size tov SVGA(800x600)
sensor.set_windowing([370,176,335,346]) #roi 300,0,200,600
sensor.set_hmirror(True)
sensor.set_vflip(True)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
#sensor.set_auto_exposure(False,35000)#设置感光度  这里至关重要
still_send_flag = 0
clock = time.clock()
red_blobs = 0
lcd.init(freq=15000000)
uart = UART(3,115200)
uart.init(115200, bits=8, parity=None, stop=1 )

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
data = 0
data_decoded  = 0
rect_point_num = 0
frame_head = '#'
frame_tail = ';'
first_recieve_flag = 1

l_value= 60
baoguang = 20000
baoguang_step = 1500
sensor.set_auto_exposure(False,baoguang)#设置感光度  这里至关重要
auto_exposure_flag = True
auto_exposure_first = True

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



while(True):
    clock.tick()                    # Update the FPS clock.
    img = sensor.snapshot()         # Take a picture and return the image.
    if uart.any():  # 如果有可读数据
        data = uart.read()  # 读取数据
        print(data)  # 输出读取到的数据
    # 计算图像的直方图
    #uart.write('#0'+'X'+'1'+'Y'+'2'+'x'+'3'+'y'+'4'+';')
    histogram = img.histogram()
    histogram_statistics = histogram.get_statistics()
    red_blobs = img.find_blobs([red_thresholds],x_stride=1, y_stride=1, pixels_threshold=5)
    #识别色块
    if red_blobs:
        red_blob = find_max_red_blobs(red_blobs,img)
        print('找到了色块')
        print("red_blobs,X:%s,Y:%s"%(red_blob.cx(),red_blob.cy()))
        img.draw_rectangle(red_blob.rect(), color = (255, 255, 255))
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
            rect_points_flag = 0 #只计算一次
            print("rect_point:",rect_points)
    #如果接收到了坐标发送信号且矩形识别完成

    histogram = img.histogram()
    histogram_statistics = histogram.get_statistics()
    #print(histogram_statistics)

    if auto_exposure_first:
        for i in range(20):
            img = sensor.snapshot()
            # 计算图像的直方图
            histogram = img.histogram()
            histogram_statistics = histogram.get_statistics()
            # 计算图像的直方图
            histogram = img.histogram()
            histogram_statistics = histogram.get_statistics()
            # 提取 mode 值
            if hasattr(histogram_statistics, "mode"):
                mode_value = histogram_statistics.mode()  # 调用 mode 方法
                print("mode 值:", mode_value)
            else:
                print("histogram_statistics 对象没有 mode 方法")

            if mode_value > 40:
                baoguang -= baoguang_step
                sensor.set_auto_exposure(False,baoguang)#设置感光度  这里至关重要
                print("亮度减小")

            elif mode_value < 30:
                baoguang += baoguang_step
                sensor.set_auto_exposure(False,baoguang)#设置感光度  这里至关重要
                print("亮度增大")
            else:
                auto_exposure_first = False
    #print("调节已结束")
    
    if data=='B' and rect_points_flag == 0:
        still_send_flag = 1
        
    elif data == 'A' and rect_points_flag == 0:
        rect_point_num += 1
        data = 0
    else:
        pass
        #print('等待接收数据')

    if still_send_flag ==1:    #持续发送坐标
        if rect_points is not None and red_blobs is not None:
            send_data = '#0'+'X'+str(rect_points[rect_point_num][0])+'Y'+str(rect_points[rect_point_num][1])+'x'+str(red_blob.cx())+'y'+str(red_blob.cy())+';'
            print(send_data)
            uart.write(send_data)
       
    #print("一次任务结束")
    fps = 'fps:'+str(clock.fps())
    #img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
   # print(clock.fps())

#方案二 ： 当激光进入顶点范围直接发送前后顶点的error_x,error_y——————————>减少代码执行量，提高效率