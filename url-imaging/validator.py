def validate_percent(percent):
	if percent < 1 or percent > 1000:
		raise ValueError('Must be between 0 and 1000: ' + str(percent))

def validate_x_y(x, y):
	if x < 0 or y < 0:
		raise ValueError('Must be positive: x=' + str(x) + ',y=' + str(y))

def validate_width_height(width, height):
	if width < 1 or height < 1 or width > 5000 or height > 5000:
		raise ValueError('Must be between 0 and 5,000: width=' + str(width) + ',height=' + str(height))
