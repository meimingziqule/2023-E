import sensor, image, time, pyb, math, lcd
from pyb import UART, LED, Pin, Timer
green_thresholds = (0, 100, 11, 91, -20, 54)
green_thresholds = (60, 100, -128, -28, -81, 68)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.SVGA)
sensor.set_windowing([330, 270, 378, 311])
sensor.set_hmirror(True)
sensor.set_vflip(True)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_contrast(2)
sensor.set_gainceiling(8)
still_send_flag = 0
clock = time.clock()
green_blobs = 0
lcd.init(freq=15000000)
uart = UART(3, 115200)
uart.init(115200, bits=8, parity=None, stop=1)
black_blob = None
black_thresholds = (0, 15, -5, 82, 1, 126)
black_roi = None
get_black_roi_flag = 1
start_flag = 1
line_num = 0
one_error_x = 0
one_error_y = 0
error_x = 0
error_y = 0
task_flag = 0
green_blob = None
i = 0
rect_flag = 1
rect_points = []
rect_points_flag = 1
green_send_data = None
buffer = ""
data = ''
data_decoded = 0
rect_point_num = 0
frame_head = '#'
frame_tail = ';'
first_recieve_flag = 1
l_value = 60
baoguang = 20000
baoguang_step = 1500
sensor.set_auto_exposure(False, baoguang)
auto_exposure_flag = True
auto_exposure_first = True
rect_points_transform = None
A_recieve_flag = 100
data_rect_points = None
#矩形坐标获取发送一次
one_rect_data_get_flag = 1
#矩形坐标发送停止标志位
one_rect_data_stop_flag = 0
#持续发送标志位
continue_send_flag = 0

data_rect_points_flag  = 1
def list_format_coordinates(coordinates):
    # 添加第一个元素到列表的末尾
    coordinates.append(coordinates[0])
    
    result = ""
    for i, (x, y) in enumerate(coordinates):
        letter = chr(65 + i)
        if i == 0:
            result += f"#{letter}X{x}Y{y},"
        else:
            result += f"{letter}X{x}Y{y},"
    result += ";"
    return result

def remove_duplicates_preserve_order(input_list):
	seen = set()
	unique_list = []
	for item in input_list:
		if item not in seen:
			seen.add(item)
			unique_list.append(item)
	return unique_list
def scale_rect_points(rect_points, scale_factor):
	x_coords = [point[0] for point in rect_points]
	y_coords = [point[1] for point in rect_points]
	center_x = sum(x_coords) / len(rect_points)
	center_y = sum(y_coords) / len(rect_points)
	scaled_points = []
	for point in rect_points:
		x = center_x + (point[0] - center_x) / scale_factor
		y = center_y + (point[1] - center_y) / scale_factor
		x = round(x, 1)
		y = round(y, 1)
		scaled_points.append((x, y))
	return scaled_points
def divide_line_segment(point1, point2, n):
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
def divide_polygon_segments(points, n):
	if len(points) != 4:
		raise ValueError("points列表必须包含四个点")
	result = []
	for i in range(4):
		segment_points = divide_line_segment(points[i], points[(i + 1) % 4], n)
		result.extend(segment_points)
	return result
def find_rect_corners(rect, img):
	for r in rect:
		corners = change_condi(r.corners())
		for p in corners:
			img.draw_cross(p[0], p[1], 5, color=(0, 255, 0))
		print(corners)
	return corners
def find_max_green_blobs(blobs, img):
	if not blobs:
		print("没有找到任何 blobs")
		return None
	try:
		green_blob = max(blobs, key=lambda b: b.pixels())
		img.draw_cross(green_blob.cx(), green_blob.cy())
		print("红色像素数量：%d" % green_blob.pixels())
		return green_blob
	except Exception as e:
		print("发生错误: ", e)
		return None
def change_condi(corners_list):
	corners = [0, 0, 0, 0]
	corners[0] = corners_list[-1]
	corners[1] = corners_list[-2]
	corners[2] = corners_list[-3]
	corners[3] = corners_list[-4]
	if corners is not None:
		return corners
def error_distance(corners, x, y):
	error_x = corners[0] - x
	error_y = corners[1] - y
	if abs(error_x) and abs(error_y):
		return error_x, error_y
	else:
		return None, None
def next_target_error(line_num, green_blobs, corners):
	one_error_x, one_error_y = error_distance(corners[line_num - 1], green_blobs.cx(), green_blobs.cy())
	return one_error_x, one_error_y
def now_conditiont(blob, corners):
	for line_num, corner in enumerate(corners):
		if (abs(blob.cx() - corner[0]) < 5) and (abs(blob.cy() - corner[1]) < 5):
			return line_num + 1
	return None
def receive_data():
	global buffer
	if uart.any():
		print("开始接收数据")
		char = uart.read(1).decode()
		print("char",char)
		if char == '#':
			buffer = ""
		elif char == ';':
			if buffer:
				data = buffer
				buffer = ""
				return data
		else:
			buffer += char
	else:
		time.sleep_ms(1)
while True:
	clock.tick()
	img = sensor.snapshot()
	green_blobs = img.find_blobs([green_thresholds], x_stride=1, y_stride=1, pixels_threshold=1)

	if green_blobs:
		green_blob = find_max_green_blobs(green_blobs, img)
		print('找到了色块')
		print("green_blobs,X:%s,Y:%s" % (green_blob.cx(), green_blob.cy()))
		img.draw_rectangle(green_blob.rect(), color=(255, 255, 255))
	'''	
	if get_black_roi_flag == 1:
		black_blobs = img.find_blobs([black_thresholds], x_stride=100, y_stride=100, pixels_threshold=5000)
		if black_blobs:
			black_blob = find_max_green_blobs(black_blobs, img)
			print('找到了黑色色块')
			print("black_blobs,X:%s,Y:%s" % (black_blob.cx(), black_blob.cy()))
			black_roi = (black_blob.rect()[0] - 5, black_blob.rect()[1] - 5, black_blob.rect()[2] + 10,
						 black_blob.rect()[3] + 10)
			img.draw_rectangle(black_roi, color=(255, 255, 255))
			if black_roi is not None:
				get_black_roi_flag = 0'''
				
	if rect_flag == 1:
		rect = img.find_rects(threshold=17000, x_gradient=20, y_gradient=20)
		if rect:
			corners = find_rect_corners(rect, img)
			if corners:
				rect_flag = 0
		else:
			print("没找到矩形")
	else:
		print("corner:", corners)
		img.draw_rectangle(rect[0].rect(), color=(255, 255, 255))
	print("rect_points_flag", rect_points_flag)

			
	if rect_points_flag == 1:
		if rect:
			rect_points = divide_polygon_segments(corners, 2)
			rect_points_transform = scale_rect_points(rect_points, 1.06)
			rect_points_transform = remove_duplicates_preserve_order(rect_points_transform)
			rect_points_flag = 0
			print("rect_point:", rect_points)
			
	print("rect_points", rect_points)
	print("rect_points_transform", rect_points_transform)
	data = receive_data()

	if data == 'B' and rect_points_flag == 0:
		one_rect_data_stop_flag = 1
		still_send_flag = 1
		LED(3).on()
		print('44444444444444444444444444444444444444')
		
	elif data == 'A' and rect_points_flag == 0:
		rect_point_num += 1
		print("111312312222221122222222222222222222222222222222222222222222222222222222222222")
	else:
		pass

	if rect_points_transform is not None:
		img.draw_cross(int(rect_points_transform[rect_point_num][0]), int(rect_points_transform[rect_point_num][1]))
		
    #这里只接受一次
	if rect_points_transform is not None and one_rect_data_get_flag == 1:
		data_rect_points = list_format_coordinates(rect_points_transform)
		print("data_rect_points:",data_rect_points)
		one_rect_data_get_flag = 0
		
	if still_send_flag ==1:
		if green_blob is not None:
			green_send_data = '#0' + 'X' + str(float(green_blob.cx())) + 'Y' + str(float(green_blob.cy())) + ';'
			uart.write(green_send_data)
			print(green_send_data)
			print('3333333333333333333333333333333333333333333333')
			
		else:
			print("没有找到色块")		
			#green_send_data = '#0' + 'X' + str(12) + 'Y' + str(32) + ';'
			#uart.write(green_send_data)
			
	#在接收到B前 一直发坐标
	elif still_send_flag == 0 and data_rect_points is not None:
		uart.write(data_rect_points)
		print("data_rect_points:",data_rect_points)
		

	fps = 'fps:' + str(clock.fps())
	img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
	print(clock.fps())
