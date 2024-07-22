import sensor, image, time, pyb,math,lcd
from pyb import UART, LED,Pin, Timer
red_thresholds = (0, 100, 11, 91, -20, 54)
green_thresholds = (0, 100, 5, 127, -61, 122)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.SVGA)
sensor.set_windowing([306,196,397,391])
sensor.set_hmirror(True)
sensor.set_vflip(True)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
sensor.set_contrast(2)
sensor.set_gainceiling(8)
still_send_flag = 0
clock = time.clock()
red_blobs = 0
lcd.init(freq=15000000)
uart = UART(3,115200)
uart.init(115200, bits=8, parity=None, stop=1 )
black_blob = None
black_thresholds = (0, 15, -5, 82, 1, 126)
black_roi = None
get_black_roi_flag = 1
start_flag = 1
line_num  = 0
one_error_x = 0
one_error_y = 0
error_x = 0
error_y = 0
task_flag = 0
red_blob = None
i=0
rect_flag  = 1
rect_points = []
rect_points_flag = 1
send_data = None
buffer = None
data = ''
data_decoded  = 0
rect_point_num = 0
frame_head = '#'
frame_tail = ';'
first_recieve_flag = 1
l_value= 60
baoguang = 30000
baoguang_step = 1500
sensor.set_auto_exposure(False,baoguang)
auto_exposure_flag = True
auto_exposure_first = True
rect_points_transform = None

A_recieve_flag = 1000
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
def find_rect_corners(rect,img):
	for r in rect:
		corners = change_condi(r.corners())
		for p in corners:
			img.draw_cross(p[0], p[1], 5, color = (0, 255, 0))
		print(corners)
	return corners
def find_max_red_blobs(blobs, img):
	if not blobs:
		print("没有找到任何 blobs")
		return None
	try:
		red_blob = max(blobs, key=lambda b: b.pixels())
		img.draw_cross(red_blob.cx(),red_blob.cy())
		print("红色像素数量：%d" % red_blob.pixels())
		return red_blob
	except Exception as e:
		print("发生错误: ", e)
		return None
def change_condi(corners_list):
	corners = [0,0,0,0]
	corners[0] = corners_list[-1]
	corners[1] = corners_list[-2]
	corners[2] = corners_list[-3]
	corners[3] = corners_list[-4]
	if corners is not None:
		return corners
def error_distance(corners,x,y):
	error_x = corners[0]-x
	error_y = corners[1]-y
	if abs(error_x) and abs(error_y):
		return error_x,error_y
	else:
		return None,None
def next_target_error(line_num,red_blobs,corners):
	one_error_x,one_error_y = error_distance(corners[line_num-1],red_blobs.cx(),red_blobs.cy())
	return one_error_x,one_error_y
def now_conditiont(blob, corners):
	for line_num, corner in enumerate(corners):
		if (abs(blob.cx() - corner[0]) < 5) and (abs(blob.cy() - corner[1]) < 5):
			return line_num + 1
	return None
def receive_data():
	global buffer
	buffer = buffer.lstrip('#')
	if uart.any():
		char = uart.read(1).decode()
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
def receive_data():
	global buffer
	buffer = buffer.lstrip('#')
	if uart.any():
		char = uart.read(1).decode()
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
buffer = ""
while True:
	clock.tick()
	img = sensor.snapshot()
	red_blobs = img.find_blobs([red_thresholds],x_stride=1, y_stride=1, pixels_threshold=5)
	if A_recieve_flag <= 1000:
		A_recieve_flag += 1
	else:print("A_recieve_flag",A_recieve_flag)
        
	if red_blobs:
		red_blob = find_max_red_blobs(red_blobs,img)
		print('找到了色块')
		print("red_blobs,X:%s,Y:%s"%(red_blob.cx(),red_blob.cy()))
		img.draw_rectangle(red_blob.rect(), color = (255, 255, 255))
	if get_black_roi_flag == 1:
		black_blobs = img.find_blobs([black_thresholds],x_stride=100, y_stride=100, pixels_threshold=5000)
		if black_blobs:
			black_blob = find_max_red_blobs(black_blobs,img)
			print('找到了黑色色块')
			print("black_blobs,X:%s,Y:%s"%(black_blob.cx(),black_blob.cy()))
			black_roi= (black_blob.rect()[0]-5,black_blob.rect()[1]-5,black_blob.rect()[2]+10,black_blob.rect()[3]+10)
			img.draw_rectangle(black_roi, color = (255, 255, 255))
			if black_roi is not None:
				  get_black_roi_flag = 0
	if rect_flag == 1:
		rect = img.find_rects(threshold = 17000)
		if rect:
			corners = find_rect_corners(rect,img)
			if corners:
				rect_flag =0
		else:
			print("没找到矩形")
	else:
		print("corner:",corners)
		img.draw_rectangle(rect[0].rect(), color = (255, 255, 255))
	print("rect_points_flag",rect_points_flag)
	if rect_points_flag == 1:
		if rect:
			rect_points = divide_polygon_segments(corners, 2)
			rect_points_transform =  scale_rect_points(rect_points,1.06)
			rect_points_transform = remove_duplicates_preserve_order(rect_points_transform)
			rect_points_flag = 0
			print("rect_point:",rect_points)
	print("rect_points",rect_points)
	print("rect_points_transform",rect_points_transform)
	data = receive_data()
	if data=='B' and rect_points_flag == 0:
		still_send_flag = 1
		LED(3).on()
	elif data == 'A' and rect_points_flag  == 0 and A_recieve_flag == 1000:
		rect_point_num += 1
		data = 'B'
		A_recieve_flag = 0
		print("111312312222221122222222222222222222222222222222222222222222222222222222222222")
	else:
		pass
	if still_send_flag ==1:
		print("still_send_flag",still_send_flag)
		if rect_points is not None and red_blobs is not None:
			if  rect_point_num<len(rect_points_transform):
				send_data = '#0'+'X'+str(rect_points_transform[rect_point_num][0])+'Y'+str(rect_points_transform[rect_point_num][1])+'x'+str(float(red_blob.cx()))+'y'+str(float(red_blob.cy()))+';'
				print(send_data)
				print('3333333333333333333333333333333333333333333333')
				uart.write(send_data)
			else:
				rect_point_num = 0
	if rect_points_transform is not None  :
		img.draw_cross(int(rect_points_transform[rect_point_num][0]),int(rect_points_transform[rect_point_num][1]))
	fps = 'fps:'+str(clock.fps())
	img.draw_string(0, 0, fps, lab=(255, 0, 0), scale=2)
	print(clock.fps())
#方案二 ： 当激光进入顶点范围直接发送前后顶点的error_x,error_y——————————>减少代码执行量，提高效率
