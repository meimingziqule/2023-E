import sensor
import image
import time

# 初始化摄像头传感器
sensor.reset()
sensor.set_pixformat(sensor.RGB565)  # 设置为灰度图像格式
sensor.set_framesize(sensor.SVGA)
l_value= 60
baoguang = 40000
baoguang_step = 3000
clock = time.clock()
sensor.set_auto_exposure(False,baoguang)#设置感光度  这里至关重要
auto_exposure_flag = True
auto_exposure_first = True
while(True):
    clock.tick()

    # 捕获图像
    img = sensor.snapshot()
    # 计算图像的直方图
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
        
            if mode_value > 80:
                baoguang -= baoguang_step
                sensor.set_auto_exposure(False,baoguang)#设置感光度  这里至关重要
                print("亮度减小")
    
            elif mode_value < 60:
                baoguang += baoguang_step 
                sensor.set_auto_exposure(False,baoguang)#设置感光度  这里至关重要
                print("亮度增大")
            else:
                auto_exposure_first = False
    print("调节已结束")           
            
    