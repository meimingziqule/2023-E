import sensor
import image
import time

# 初始化摄像头传感器
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.SVGA)
baoguang = 10000
baoguang_step = 2000
clock = time.clock()

while(True):
    clock.tick()

    # 捕获图像
    img = sensor.snapshot()
