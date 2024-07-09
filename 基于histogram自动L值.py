import sensor
import image
import time

# 初始化摄像头传感器
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)  # 设置为灰度图像格式
sensor.set_framesize(sensor.SVGA)
baoguang = 10000
baoguang_step = 2000
clock = time.clock()

while(True):
    clock.tick()

    # 捕获图像
    img = sensor.snapshot()
    
    # 计算图像的直方图
    histogram = img.histogram()
    histogram_statistics = histogram.get_statistics()
    print(histogram_statistics)
    
    # 提取 median 值
    if hasattr(histogram_statistics, "median"):
        median_value = histogram_statistics.median()  # 调用 median 方法
        print("Median 值:", median_value)
    else:
        print("histogram_statistics 对象没有 median 方法")
