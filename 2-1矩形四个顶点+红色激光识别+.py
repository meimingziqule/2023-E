import sensor, image, time, pyb,math,lcd    
from pyb import UART, LED,Pin, Timer
# 50kHz pin6 timer2 channel1
light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
light.pulse_width_percent(50) # 控制亮度 0~100

red_thresholds = (32, 88, 7, 74, -6, 127)# 通用红色阈值
green_thresholds = (0, 38, 0, 124, -128, 127)# 通用绿色阈值   待修改
sensor.reset()                     
sensor.set_pixformat(sensor.RGB565) 
sensor.set_framesize(sensor.SVGA)   # Set frame size tov SVGA(800x600)
sensor.set_windowing([300,0,200,600])  #roi 300,0,200,600
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
#  #1是十字路口    #2是终点

def change_condi(corners_list):
    corners = [0,0,0,0]
    corners[0] = corners_list[-1]
    corners[1] = corners_list[-2]
    corners[2] = corners_list[-3]
    corners[3] = corners_list[-4]
    return corners


def error_distance(corners_list,x,y):
    error_x = corners_list[0][0]-x
    error_y = corners_list[0][1]-y
    return error_x,error_y

def reach_condi(corner_list,x,y):
    if x < corner_list[0]+5 and x > corner_list[0]-5 and y > corner_list[0][1]-5 and y < corner_list[0][1]+5:
        return True


while(True):
    clock.tick()                    # Update the FPS clock.
    img = sensor.snapshot()         # Take a picture and return the image.
    red_blobs = img.find_blobs([red_thresholds],x_stride=5, y_stride=5, pixels_threshold=50) 

    for blob in red_blobs:
        print("x:%d,y:%d,w:%d,h:%d"%(blob.cx(),blob.cy(),blob.w(),blob.h()))
        img.draw_rectangle(blob.rect())
        print("红色像素数量：%d"%blob.pixels())
        print(len(red_blobs))##这里后面加个保护



    for r in img.find_rects(threshold = 10000):
        img.draw_rectangle(r.rect(), color = (255, 0, 0))
        corners = change_condi(r.corners())
        for p in corners:  # 颠倒点的顺序
            img.draw_circle(p[0], p[1], 5, color = (0, 255, 0))
            #print("-1",cor)
            #print('1',corners)
            print(corners)
    
    #1.计算激光和顶点坐标的差距，串口返回下x,y的差距值
    
    
    for i in range(4):
        reach_flag = reach_condi(corners[i],red_blobs.cx(),red_blobs.cy())
        



    fps = 'fps:'+str(clock.fps())
    img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
    print(clock.fps())