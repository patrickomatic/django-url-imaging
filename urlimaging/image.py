import re, os
from math import atan, degrees
from PIL import Image, ImageChops, ImageFilter, ImageDraw, ImageFont
from urlimaging.validator import *

TEN_MBS = 10 * 1024 * 1024 * 1024
RGB_ONLY_FORMATS = set(['.jpg', '.jpeg'])


def with_image(fn):
	""" Decorator that handles the open and closing of an image.  """
	def process(*args):
		img = fn(Image.open(args[0]), *args[1:])

		ext = os.path.splitext(args[0])[1].lower()
		if ext in RGB_ONLY_FORMATS and img.mode != 'RGB':
			img = img.convert('RGB')

		img.save(args[0], quality=95)
	return process


@with_image
def resize(img, width, height):
	width, height = int(width), int(height)
	validate_width_height(width, height)
	return img.resize((int(width), int(height)), Image.ANTIALIAS)


@with_image
def scale(img, percent):
	percent = int(percent)
	validate_percent(percent)

	p = percent * 0.01

	w, h = img.size
	return img.resize((int(w * p), int(h * p)), Image.ANTIALIAS)


@with_image
def fit(img, width, height):
	img.thumbnail((int(width), int(height)), Image.ANTIALIAS)
	return img


@with_image
def width(img, width):
	w, h = img.size
	return img.resize((int(width), int(float(h) * (float(width) / float(w)))), Image.ANTIALIAS)


@with_image
def height(img, height):
	w, h = img.size
	return img.resize((int(float(w) * (float(height) / float(h))), int(height)), Image.ANTIALIAS)


@with_image
def square(img, size):
	size = int(size)
	validate_width_height(size, size)

	width, height = img.size

	half_size = size / 2.0
	# already square?
	if width == height:
		img = img.resize((size, size), Image.ANTIALIAS)
		return img
	elif width > height:
		# resize proportionally to get height == size
		resize_amount = float(size) / float(height)
		width = int(width * resize_amount)
		img = img.resize((width, size), Image.ANTIALIAS)

		return img.crop((int(width / 2.0 - half_size), 0, int(width / 2.0 + half_size), size))
	else:
		# get width == size
		resize_amount = float(size) / float(width)
		height = int(height * resize_amount)
		img = img.resize((size, height), Image.ANTIALIAS)

		return img.crop((0, int(height / 2.0 - half_size), size, int(height / 2.0 + half_size)))


@with_image
def crop(img, x, y, width, height):
	x, y, width, height = int(x), int(y), int(width), int(height)
	validate_x_y(x, y)
	validate_width_height(width, height)

	return img.crop((x, y, x + width, y + height))


@with_image
def rotate(img, degrees):
	return img.rotate(-int(degrees))


@with_image
def thumbnail(img, size):
	THUMBNAIL_SIZES = { 
		'small': 64,
		'medium': 96,
		'large': 128,
	}

	if size.isdigit():
		s = int(size)
	elif size in THUMBNAIL_SIZES:
		s = THUMBNAIL_SIZES[size]
	else:
		s = THUMBNAIL_SIZES['medium']

	img.thumbnail((s, s), Image.ANTIALIAS)
	return img


@with_image
def black_and_white(img):
	return img.convert('L')


@with_image
def invert(img):
	return ImageChops.invert(img)


@with_image
def blur(img):
	return img.filter(ImageFilter.BLUR)

@with_image
def sharpen(img):
	return img.filter(ImageFilter.SHARPEN)


def convert(filename, format):
	img = Image.open(filename)
	if img.mode != 'RGB':
		img = img.convert('RGB')

	# for some reason this chokes on 'JPG'
	format = format.upper()
	if format == 'JPG':
		format = 'JPEG'

	img.save(filename, format, quality=95)


FONT = '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'

@with_image
def watermark(img, text):
	if img.mode != 'RGB':
		img = img.convert('RGB')

	watermark = Image.new('RGBA', (img.size[0], img.size[1]))
	draw = ImageDraw.ImageDraw(watermark, 'RGBA')

	size = 0
	while True:
		size += 1
		nextFont = ImageFont.truetype(FONT, size)
		nextTextWidth, nextTextHeight = nextFont.getsize(text)
		if nextTextWidth + nextTextHeight / 3 > watermark.size[0]:
			break
		font = nextFont
		textWidth, textHeight = nextTextWidth, nextTextHeight
	
	draw.text(((watermark.size[0] - textWidth) / 2,
			(watermark.size[1] - textHeight) / 2), text, font=font, fill=(255,255,255))

	watermark = watermark.rotate(degrees(atan(float(img.size[1]) /
					img.size[0])), Image.BICUBIC)
	mask = watermark.convert('L').point(lambda x: min(x, 55))
	watermark.putalpha(mask)
	img.paste(watermark, None, watermark)

	return img


HTML_COLORS = { 
	'aqua': (0, 255, 255),
	'cyan': (0, 255, 255),
	'black': (0, 0, 0),
	'blue': (0, 0, 255),
	'fuchsia': (255, 0, 255),
	'magenta': (255, 0, 255),
	'gray': (128, 128, 128),
	'grey': (128, 128, 128),
	'green': (0, 128, 0),
	'lime': (0, 255, 0),
	'maroon': (128, 0, 0),
	'navy': (0, 0, 128),
	'olive': (128, 128, 0),
	'purple': (128, 0, 128),
	'red': (255, 0, 0),
	'silver': (192, 192, 192),
	'teal': (0, 128, 128),
	'white': (255, 255, 255),
	'yellow': (255, 255, 0),
}

def color_to_rgb(color):
	try:
		return HTML_COLORS[color.lower()]
	except KeyError:
		return None

def hex_to_decimal(h):
	return int(h, 16)

def hex_to_rgb(hex):
	""" Convert a hexadecimal triplet to an RGB tuple """

	if hex.startswith("#"):
		hex = hex[1:]

	try:
		if len(hex) == 3:
			hex_triplet = map(lambda x: "%s%s" % (x, x), tuple(hex))
			return tuple(map(hex_to_decimal, hex_triplet))
		elif len(hex) == 6:
			return tuple(map(hex_to_decimal, (hex[0:2], hex[2:4], hex[4:6])))
	except ValueError:
		pass

	return None


@with_image
def background(img, color):
	rgb = hex_to_rgb(color)
	if not rgb: rgb = color_to_rgb(color)
	if not rgb: return None

	img = img.convert('RGBA')
	overlayed = Image.new('RGBA', img.size)
	overlayed.paste(rgb)
	overlayed.paste(img, mask=img)

	return overlayed


COMMANDS = [ { 
		'regex': re.compile(r'^resize/(\d+)x(\d+)/', re.I),
		'fn': resize, 
		'title': 'Resize',
		'anchor_name': 'resize',
		'description': 'Resize an image.',
		'format': '<tt>/resize/WIDTHxHEIGHT/IMAGEURL</tt>',
		'arguments': [ 
			('WIDTHxHEIGHT', 'The width and height of the desired image. Expressed as a width and height specification of the form WIDTHxHEIGHT where WIDTH and HEIGHT are both positive numbers.') 
		],
	}, {
		'regex': re.compile(r'^scale/(\d+)/', re.I),
		'fn': scale, 
		'title': 'Scale',
		'anchor_name': 'scale',
		'description': 'Scale an image proportionally by a given percentage',
		'format': '<tt>/scale/PERCENT/IMAGEURL</tt>',
		'arguments': [ 
			('PERCENT', 'A value between 0 and 1000 by which to scale the image.  If greater than 100, the image will be increased in size by that percentage amount.') 
		],
	}, {
		'regex': re.compile(r'^width/(\d+)/', re.I),
		'fn': width, 
		'title': 'Width',
		'anchor_name': 'width',
		'description': 'Scale an image proportionaly to the given width',
		'format': '<tt>/width/SIZE/IMAGEURL</tt>',
		'arguments': [ ('SIZE', 'A positive number specifying the target width of the image.') ],
	}, {
		'regex': re.compile(r'^height/(\d+)/', re.I),
		'fn': height, 
		'title': 'Height',
		'anchor_name': 'height',
		'description': 'Scale an image proportionaly to the given height',
		'format': '<tt>/height/SIZE/IMAGEURL</tt>',
		'arguments': [ 
			('SIZE', 'A positive number specifying the target height of the image.') 
		],
	}, {
		'regex': re.compile(r'^fit/(\d+)x(\d+)/', re.I),
		'fn': fit, 
		'title': 'Fit',
		'anchor_name': 'fit',
		'description': 'Fit an image proportionally to be within a given size',
		'format': '<tt>/fit/WIDTHxHEIGHT/IMAGEURL</tt>',
		'arguments': [ 
			('WIDTHxHEIGHT', 'The box that the image must be resized to fit into. Expressed as a width and height specification of the form WIDTHxHEIGHT where WIDTH and HEIGHT are both positive numbers.') 
		],
	}, {
		'regex': re.compile(r'^thumb(?:nail)?/(small|medium|large|\d+)/', re.I),
		'fn': thumbnail, 
		'title': 'Thumbnail',
		'anchor_name': 'thumbnail',
		'description': 'Create a thumbnail of an image',
		'format': """<tt>/thumbnail/SIZE/IMAGEURL</tt>
				or a shorter version:
			     <tt>/thumb/SIZE/IMAGEURL</tt>""",
		'arguments': [ ('SIZE', 'A number of pixels or a value of either "small" (64 pixels), "medium" (96 pixels) or "large" (128).') ],
	}, {
		'regex': re.compile(r'^square/(\d+)/', re.I),
		'fn': square, 
		'title': 'Square',
		'anchor_name': 'square',
		'description': 'Create a squared version of an image.  This will resize and crop an image to create a squared version with the height and width given.',
		'format': '<tt>/square/SIZE/IMAGEURL</tt>',
		'arguments': [ 
			('SIZE', 'The height and width of the desired square'), 
		],
	}, {
		'regex': re.compile(r'^rotate/(-?\d+)/', re.I),
		'fn': rotate, 
		'title': 'Rotate',
		'anchor_name': 'rotate',
		'description': 'Rotate an image',
		'format': '<tt>/rotate/DEGREES/IMAGEURL</tt>',
		'arguments': [ 
			('DEGREES', 'A value specifying the number of degrees that the image is to be rotated in a clockwise direction.  A negative number will rotate the image in a counter-clockwise direction.') 
		],
	}, {
		'regex': re.compile(r'^crop/(\d+),(\d+),(\d+)x(\d+)/', re.I),
		'fn': crop, 
		'title': 'Crop',
		'anchor_name': 'crop',
		'description': 'Select a rectangular region of an image and remove everything outside of that region.',
		'format': '<tt>/crop/CORNER-X,CORNER-Y,WIDTHxHEIGHT/IMAGEURL</tt>',
		'arguments': [ 
			('CORNER-X', 'The x coordinate of the bottom left corner of the rectangle to be cropped.'),
			('CORNER-Y', 'The y coordinate of the bottom left corner of the rectangle to be cropped.'),
			('WIDTH', 'The width of the rectangle to be cropped.'),
			('HEIGHT', 'The height of the rectangle to be cropped.'),
		],
	}, {
		'regex': re.compile(r'^(?:watermark|wm)/([^/]+)/', re.I),
		'fn': watermark, 
		'title': 'Watermark',
		'anchor_name': 'watermark',
		'description': 'Overlay some text on the image',
		'format': '<tt>/wm/TEXT/IMAGEURL</tt> or <tt>/watermark/TEXT/IMAGEURL</tt>',
		'arguments': [ 
			('TEXT', 'The text of the watermark.'),
		],
		'note': 'It is recommended that after generating the watermarked image, you remove the original image.  Otherwise it will continue to be publicly available.'
	}, {
		'regex': re.compile(r'^(?:blackwhite|bw)/', re.I),
		'fn': black_and_white, 
		'title': 'Black & White',
		'anchor_name': 'blackwhite',
		'description': 'Convert the image to black and white',
		'format': '<tt>/bw/IMAGEURL</tt> or <tt>/blackwhite/IMAGEURL</tt>',
		'arguments': [ ],
	}, {
		'regex': re.compile(r'^invert/', re.I),
		'fn': invert, 
		'title': 'Invert',
		'anchor_name': 'invert',
		'description': 'Invert the color profile of the image',
		'format': '<tt>/invert/IMAGEURL</tt>',
		'arguments': [ ],
	}, {
		'regex': re.compile(r'^blur/', re.I),
		'fn': blur, 
		'title': 'Blur',
		'anchor_name': 'blur',
		'description': 'Apply a blurring filter to the image',
		'format': '<tt>/blur/IMAGEURL</tt>',
		'arguments': [ ],
	}, {
		'regex': re.compile(r'^sharpen/', re.I),
		'fn': sharpen, 
		'title': 'Sharpen',
		'anchor_name': 'sharpen',
		'description': 'Apply a sharpening filter to the image',
		'format': '<tt>/sharpen/IMAGEURL</tt>',
		'arguments': [ ],
	}, {
		'regex': re.compile(r'^convert/\.?(bmp|gif|im|jpe?g|msp|pcx|pdf|png|ppm|tiff|xbm)/', re.I),
		'fn': convert, 
		'title': 'Convert',
		'anchor_name': 'convert',
		'description': 'Convert the image to a different format',
		'format': '<tt>/convert/FORMAT/IMAGEURL</tt>',
		'arguments': [ 
			('FORMAT', 'The desired image format of the created image.  Allowable values are: bmp, gif, im, jpeg/jpg, msp, pcx, pdf, png, ppm, tiff, xbm')
		],
	}, {
		'regex': re.compile(r'^background/(\w+)/', re.I),
		'fn': background, 
		'title': 'Background',
		'anchor_name': 'background',
		'description': 'Set a custom background color.  The image must support transparency.',
		'format': '<tt>http://urlimg.com/background/FORMAT/IMAGEURL</tt>',
		'arguments': [ 
			('FORMAT', 'Either a color (red, green, blue, etc..) or a hexadecimal triplet (#FF00FF).')
		],
	}, 
]

