import sensor, image, time, pyb,math,lcd    
from pyb import UART, LED,Pin, Timer
# 50kHz pin6 timer2 channel1
light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
light.pulse_width_percent(50) # 控制亮度 0~100

red_thresholds = (95, 100, 0, 19, -6, 9)# 通用红色阈值
green_thresholds = (0, 38, 0, 124, -128, 127)# 通用绿色阈值   待修改
sensor.reset()                     
sensor.set_pixformat(sensor.RGB565) 
sensor.set_framesize(sensor.SVGA)   # Set frame size tov SVGA(800x600)
sensor.set_windowing([408,125,377,355])  #roi 300,0,200,600
sensor.set_hmirror(True)
sensor.set_vflip(True)
sensor.skip_frames(time = 2000)    
sensor.set_auto_gain(False) 
sensor.set_auto_whitebal(False)    
sensor.set_auto_exposure(False,8000)#设置感光度

clock = time.clock()
red_blbos = 0
lcd.init(freq=15000000)
uart = UART(3,115200)  
uart.init(115200, bits=8, parity=None, stop=1 )

def find_rect_corners(rect,img):
    for r in rect:
        img.draw_rectangle(r.rect(), color = (255, 0, 0))
        corners = change_condi(r.corners())
        for p in corners:  # 颠倒点的顺序
            img.draw_circle(p[0], p[1], 5, color = (0, 255, 0))
            print(corners)#打印顶点[(x1,y1),................]
    return corners        
def find_red_blobs(blobs, img):
    if not blobs:
        print("没有找到任何 blobs")
        return None
    
    try:
        red_blob = max(blobs, key=lambda b: b.pixels())
        print("x:%d,y:%d,w:%d,h:%d" % (red_blob.cx(), red_blob.cy(), red_blob.w(), red_blob.h()))
        img.draw_rectangle(red_blob.rect())
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

#求error_x error_y
def error_distance(corners,x,y):
    error_x = corners[0]-x
    error_y = corners[1]-y
    return error_x,error_y  ##？？？？

#判断激光是否到达
def reach_condi(corner_list,x,y):
    if x < corner_list[0]+5 or x > corner_list[0]-5 and y > corner_list[1]-5 or y < corner_list[1]+5:
        return True
    else:
        return False

while(True):
    clock.tick()                    # Update the FPS clock.
    img = sensor.snapshot()         # Take a picture and return the image.
    red_blobs = img.find_blobs([red_thresholds],x_stride=1, y_stride=1, pixels_threshold=1)
    if red_blobs:
        red_blob = find_red_blobs(red_blobs,img)
    else:
        print("没找到色块")
    rect = img.find_rects(threshold = 10000)
    if rect:
        corners = find_rect_corners(rect,img)#找顶点[(x1,y1),................]
    else:
        print("没找到矩形")
    #1.计算激光和顶点坐标的差距，串口返回下x,y的差距值
    #2.根据差距值，控制激光的位置，使其到达目标点
    #3.等待目标点到达，然后再次检查条件
    for i in range(4):
        # 当 reach_condi 条件满足时，执行以下代码
        while True:
            #第一次发送找到2矩形框
            if corners and red_blobs:
                error_x, error_y = error_distance(corners[i], red_blob.cx(), red_blob.cy())
                uart.write(str(abs(error_x)) + "," + str(abs(error_y)))  # 发送数据
            if corners and red_blobs:
                if reach_condi(corners[i], red_blob.cx(), red_blob.cy()):
                    break
            # 等待一段时间后再次检查条件
            #time.sleep(0.1)
    print("发送任务已完成")
    fps = 'fps:'+str(clock.fps())
    img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
    print(clock.fps())