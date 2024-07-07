import sensor, image, time
#rect.corners()
#返回一个有四个元组的列表，每个元组代表矩形的四个顶点（x, y）.从左上角的顶点开始，按照顺时针排序。

#rect.rect()
#返回检测到的矩形的外接长方形的(x, y, w, h)。

#rect.magnitude()
#返回检测到矩形的大小。

def change_condi(corners_list):
    corners = [0,0,0,0]
    corners[0] = corners_list[-1]
    corners[1] = corners_list[-2]
    corners[2] = corners_list[-3]
    corners[3] = corners_list[-4]
    return corners
    


#######这里注意一下得更换一下矩形四个顶点的位置  因为画面颠倒了导致反了
sensor.reset()                     
sensor.set_pixformat(sensor.RGB565) 
sensor.set_framesize(sensor.SVGA)   # Set frame size tov SVGA(800x600)
sensor.set_windowing([466,330,156,178])  #roi 300,0,200,600
sensor.set_hmirror(True)
sensor.set_vflip(True)
sensor.skip_frames(time = 2000)    
sensor.set_auto_gain(False) 
sensor.set_auto_whitebal(False)    
#sensor.set_auto_exposure(False,8000)#设置感光度
clock = time.clock()

while(True):
    clock.tick()
    img = sensor.snapshot()

    # 下面的`threshold`应设置为足够高的值，以滤除在图像中检测到的具有
    # 低边缘幅度的噪声矩形。最适用与背景形成鲜明对比的矩形。

    for r in img.find_rects(threshold = 10000):
        img.draw_rectangle(r.rect(), color = (255, 0, 0))
        corners = change_condi(r.corners())
        for p in corners:  # 颠倒点的顺序
            img.draw_circle(p[0], p[1], 5, color = (0, 255, 0))
            #print("-1",cor)
            #print('1',corners)
            print(corners)

    print("FPS %f" % clock.fps())
