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

    while(True):
        clock.tick()                    # Update the FPS clock.
        img = sensor.snapshot()         # Take a picture and return the image.
        red_blobs = img.find_blobs([red_thresholds],x_stride=5, y_stride=5, pixels_threshold=5) 
        for blob in red_blobs:
            print("x:%d,y:%d,w:%d,h:%d"%(blob.cx(),blob.cy(),blob.w(),blob.h()))
            img.draw_rectangle(blob.rect())
            print("红色像素数量：%d"%blob.pixels())
            print(len(red_blobs))
        fps = 'fps:'+str(clock.fps())
        img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
        print(clock.fps())
        #green_blobs = img.find_blobs([green_thresholds],x_stride=5, y_stride=5, pixels_threshold=10)
    # for blob in green_blobs:
    #        print("x:%d,y:%d,w:%d,h:%d"%(blob.cx(),blob.cy(),blob.w(),blob.h()))
    #       img.draw_rectangle(blob.rect())
    #      print("绿色像素数量：%d"%blob.pixels())  