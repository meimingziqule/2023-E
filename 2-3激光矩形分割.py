import sensor, image, time, pyb,math,lcd
from pyb import UART, LED,Pin, Timer
# 50kHz pin6 timer2 channel1
#light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
#light.pulse_width_percent(50) # 控制亮度 0~100

red_thresholds = (0, 100, 18, 118, -19, 127)# 通用红色阈值
green_thresholds = (0, 100, 5, 127, -61, 122)# 通用绿色阈值   待修改
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.SVGA)   # Set frame size tov SVGA(800x600)
sensor.set_windowing([327,187,317,320])  #roi 300,0,200,600
sensor.set_hmirror(True)
sensor.set_vflip(True)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_auto_exposure(False,35000)#设置感光度  这里至关重要

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

red_blob = None

rect_flag  = 1
rect_points = []
rect_points_flag = 1
send_data = None
#线段分割函数
def divide_line_segment(point1, point2, n):
    """
    将两个点连成的线段平分成n份，并返回包含这些点的数组。

    参数:
    point1 (tuple): 第一个点的坐标 (x1, y1)
    point2 (tuple): 第二个点的坐标 (x2, y2)
    n (int): 要平分的份数

    返回:
    list: 包含所有点的数组，例如[(x1, y1), (x2, y2), ...]
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

    #识别矩形
    if rect_flag ==1:
        rect = img.find_rects(threshold = 10000)
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
    if rect_points_flag == 1:
        if rect:
            rect_points = divide_polygon_segments(corners, 2)#如[(0.0, 0.0), (10.0, 1.2), (20.0, 2.4), (30.0, 3.6), (40.0, 4.8), (50.0, 6.0), (50.0, 6.0), (48.0, 10.8)]
            rect_points_flag = 0 #只计算一次
            print("rect_point:",rect_points)        
    if rect_points is not None:
        for i in range(len(rect_points)):
            red_blobs = img.find_blobs([red_thresholds],x_stride=1, y_stride=1, pixels_threshold=1)
            if red_blobs:
                red_blob = find_max_red_blobs(red_blobs,img)
                print('找到了色块')
                print("red_blobs,X:%s,Y:%s"%(red_blob.cx(),red_blob.cy()))
                img.draw_rectangle(red_blob.rect(), color = (255, 255, 255))
                send_data = '#0x00'+'X'+str(rect_points[i][0])+'Y'+str(rect_points[i][1])+'X'+str(red_blob.cx())+'Y'+str(red_blob.cy())+';'
                print(send_data)
                uart.write(send_data)
            else:
                pass
    print("一次任务结束")
    fps = 'fps:'+str(clock.fps())
    #img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
    print(clock.fps())

#方案二 ： 当激光进入顶点范围直接发送前后顶点的error_x,error_y——————————>减少代码执行量，提高效率

#识别色块---识别矩形框---start_flag==1且识别都成功-----计算第一次误差（将激光点置位于矩形框上）---若识别都成功，判断当前激光位置---若位于四个顶点则计算下一次目标点的误差并发送数据---若不在四个顶点则继续执行下一次while()
