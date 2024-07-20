import sensor
import image
import time

# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.RGB565)  # 使用灰度图像
sensor.set_framesize(sensor.QVGA)       # 设置图像大小为QVGA (320x240)
sensor.skip_frames(time=2000)           # 等待摄像头稳定
sensor.set_windowing((142, 45, 111, 93))
# 定义寻找最大黑色色块的函数
def find_largest_black_blob(img):
    blobs = img.find_blobs([(0, 50)], area_threshold=100)  # 寻找黑色色块，阈值范围为0-50
    if blobs:
        largest_blob = max(blobs, key=lambda b: b.area())  # 找到面积最大的色块
        return largest_blob
    return None

# 主循环
while True:
    img = sensor.snapshot()  # 获取当前帧

    largest_blob = find_largest_black_blob(img)
    if largest_blob:
        # 计算放大1.5倍后的外接框
        x = largest_blob.x() - int(largest_blob.w() * 0.25)
        y = largest_blob.y() - int(largest_blob.h() * 0.25)
        w = int(largest_blob.w() * 1.5)
        h = int(largest_blob.h() * 1.5)

        # 确保窗口坐标和大小在有效范围内
        x = max(0, x)
        y = max(0, y)
        w = min(w, img.width() - x)
        h = min(h, img.height() - y)

        # 设置窗口
        sensor.set_windowing((x, y, w, h))

        # 绘制放大后的外接框
        img.draw_rectangle([x, y, w, h], color=255)

