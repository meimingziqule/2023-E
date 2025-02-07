import sensor, image, time, pyb,math,lcd
from pyb import UART, LED,Pin, Timer
# 50kHz pin6 timer2 channel1
#light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
#light.pulse_width_percent(50) # 控制亮度 0~100

red_thresholds = (0, 100, 18, 118, -19, 127)# 通用红色阈值
green_thresholds = (0, 38, 0, 124, -128, 127)# 通用绿色阈值   待修改
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.SVGA)   # Set frame size tov SVGA(800x600)
sensor.set_windowing([327,187,317,320])  #roi 300,0,200,600
sensor.set_hmirror(True)
sensor.set_vflip(True)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_auto_exposure(False,12000)#设置感光度

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

rect_flag  = 1



def find_rect_corners(rect,img):
    for r in rect:
        #img.draw_rectangle(r.rect(), color = (255, 0, 0))
        corners = change_condi(r.corners())
        for p in corners:  # 颠倒点的顺序
            img.draw_cross(p[0], p[1], 5, color = (0, 255, 0))
        print(corners)#打印顶点[(x1,y1),................]
    return corners
def find_red_blobs(blobs, img):
    if not blobs:
        print("没有找到任何 blobs")
        return None

    try:
        red_blob = max(blobs, key=lambda b: b.pixels())
        print("x:%d,y:%d,w:%d,h:%d" % (red_blob.cx(), red_blob.cy(), red_blob.w(), red_blob.h()))
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
    if line_num == 2:
        one_error_x,one_error_y = error_distance(corners[1],red_blobs.cx(),red_blobs.cy())
    elif line_num == 3:
        one_error_x,one_error_y = error_distance(corners[2],red_blobs.cx(),red_blobs.cy())
    elif line_num == 4:
        one_error_x,one_error_y = error_distance(corners[3],red_blobs.cx(),red_blobs.cy())
    return one_error_x,one_error_y
#判断下一次该发送哪个次顶点
def now_conditiont(blob, corners):
    for line_num, corner in enumerate(corners):
        if (abs(blob.cx() - corner[0]) < 5) and (abs(blob.cy() - corner[1]) < 5):
            return line_num + 2
    return None  # 如果没有找到匹配的角落，返回 None



while(True):
    clock.tick()                    # Update the FPS clock.
    img = sensor.snapshot()         # Take a picture and return the image.
    red_blobs = img.find_blobs([red_thresholds],x_stride=1, y_stride=1, pixels_threshold=1)
    if red_blobs:
        red_blob = find_red_blobs(red_blobs,img)
    else:
        print("没找到色块")

    if rect_flag ==1:
        rect = img.find_rects(threshold = 10000)
        if rect:
            corners = find_rect_corners(rect,img)#找顶点[(x1,y1),................]
            if corners:
                rect_flag =0
        else:
            print("没找到矩形")
    else:
        print(corners)
        img.draw_rectangle(rect[0].rect(), color = (255, 0, 0))

    print("一次任务结束")
    fps = 'fps:'+str(clock.fps())
    #img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
    print(clock.fps())

#方案二 ： 当激光进入顶点范围直接发送前后顶点的error_x,error_y——————————>减少代码执行量，提高效率

#识别色块---识别矩形框---start_flag==1且识别都成功-----计算第一次误差（将激光点置位于矩形框上）---若识别都成功，判断当前激光位置---若位于四个顶点则计算下一次目标点的误差并发送数据---若不在四个顶点则继续执行下一次while()
