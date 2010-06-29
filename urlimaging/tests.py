import sys, datetime, mox
from django.core import mail
from django.test import TestCase
from django.test.client import Client
from urlimaging.models import *
from urlimaging.validator import *
import boto.s3.key


GOOD_IMAGE = 'patrickomatic.com/photography/brewing.jpg'

class CommandRunnerTest(TestCase):
	fixtures = ['image']

	def setUp(self):
		self.cr = CommandRunner()
		self.mox = mox.Mox()
		self.site = Site.objects.get(domain_name='patrickomatic.com')

	def tearDown(self):
		self.mox.UnsetStubs()


	def test_parse_url__resize(self):
		self.assert_good_urls([
				'resize/50x50/' + GOOD_IMAGE,
				'resize/1x1/www.google.com/Logos/Brewing.jpg',
		])

	def test_parse_url__scale(self):
		self.assert_good_urls([
				'scale/1/' + GOOD_IMAGE,
				'scale/50/' + GOOD_IMAGE,
				'scale/500/' + GOOD_IMAGE,
		])

	def test_parse_url__scale_bad(self):
		self.assert_bad_urls([
				'scale/x/' + GOOD_IMAGE,
				'scale/50/a.jpg',
				'scale/500',
		])

	def test_parse_url__width(self):
		self.assert_good_urls([
				'width/100/' + GOOD_IMAGE,
		])

	def test_parse_url__width_bad(self):
		self.assert_bad_urls([
				'width/x/' + GOOD_IMAGE,
				'width/' + GOOD_IMAGE,
		])

	def test_parse_url__height(self):
		self.assert_good_urls([
				'height/100/' + GOOD_IMAGE,
		])

	def test_parse_url__height_bad(self):
		self.assert_bad_urls([
				'height/x/' + GOOD_IMAGE,
				'height/' + GOOD_IMAGE,
		])

	def test_parse_url__fit(self):
		self.assert_good_urls([
				'fit/100x100/' + GOOD_IMAGE,
		])

	def test_parse_url__fit_bad(self):
		self.assert_bad_urls([
				'fit/x/' + GOOD_IMAGE,
				'fit/-1x100/' + GOOD_IMAGE,
				'fit/' + GOOD_IMAGE,
				'fit/48x48/a.jpg',
		])

	def test_parse_url__thumb(self):
		self.assert_good_urls([ 
				'thumb/small/' + GOOD_IMAGE,
				'thumb/medium/' + GOOD_IMAGE,
				'thumb/large/' + GOOD_IMAGE,
				'thumb/50/' + GOOD_IMAGE,
				'thumb/180/' + GOOD_IMAGE,
		])

	def test_parse_url__thumb_bad(self):
		self.assert_bad_urls([
				'thumb/' + GOOD_IMAGE,
				'thumbnail/' + GOOD_IMAGE,
		])

	def test_parse_url__square(self):
		self.assert_good_urls([ 
				'square/180/' + GOOD_IMAGE,
				'square/1/' + GOOD_IMAGE,
		])

	def test_parse_url__square_bad(self):
		self.assert_bad_urls([
				'square/x/' + GOOD_IMAGE,
				'square/-1/' + GOOD_IMAGE,
		])

	def test_parse_url__rotate(self):
		self.assert_good_urls([ 
				'rotate/180/' + GOOD_IMAGE,
				'rotate/-80/' + GOOD_IMAGE,
				'rotate/540/' + GOOD_IMAGE,
		])

	def test_parse_url__crop(self):
		self.assert_good_urls([ 
				'crop/50,50,100x100/' + GOOD_IMAGE,
				'crop/100,100,25x25/' + GOOD_IMAGE,
		])

	def test_parse_url__bw(self):
		self.assert_good_urls([ 
				'bw/' + GOOD_IMAGE,
				'blackwhite/' + GOOD_IMAGE,
		])

	def test_parse_url__invert(self):
		self.assert_good_urls([ 
				'invert/' + GOOD_IMAGE,
		])

	def test_parse_url__blur(self):
		self.assert_good_urls([ 
				'blur/' + GOOD_IMAGE,
		])

	def test_parse_url__sharpen(self):
		self.assert_good_urls([ 
				'sharpen/' + GOOD_IMAGE,
		])

	def test_parse_url__convert(self):
		self.assert_good_urls([ 
				'convert/png/' + GOOD_IMAGE,
				'convert/jpg/' + GOOD_IMAGE,
				'convert/jpeg/' + GOOD_IMAGE,
				'convert/JPEG/' + GOOD_IMAGE,
				'convert/PNG/' + GOOD_IMAGE,
		])

	def test_parse_url__convert_bad(self):
		self.assert_bad_urls([ 
				'convert/pg/' + GOOD_IMAGE,
				'convert/g/' + GOOD_IMAGE,
				'convert/20/' + GOOD_IMAGE,
		])

	def test_parse_url__watermark(self):
		self.assert_good_urls([ 
				'wm/some+stuff/' + GOOD_IMAGE,
				'wm/patrickomatic.com/' + GOOD_IMAGE,
				'watermark/patrickomatic.com/' + GOOD_IMAGE,
		])

	def test_parse_url__combined(self):
		self.assert_good_urls([ 
				'crop/50,50,100x100/bw/resize/50x50/rotate/180/square/50/blur/sharpen/convert/png/' + GOOD_IMAGE,
				'square/500/resize/1000x1000/bw/sharpen/blur/square/60/square/60/' + GOOD_IMAGE,
				])

	def assert_good_urls(self, urls):
		for url in urls:
			self.cr = CommandRunner()	
			self.cr.parse_url(url)
			self.assert_(self.cr.todo)

	def assert_bad_urls(self, urls):
		for url in urls:
			self.cr = CommandRunner()	
			self.cr.parse_url(url)
			self.assertFalse(self.cr.todo)


	def test_run_commands(self):
		self.__mock_s3()

		cr = CommandRunner()
		cr.parse_url('resize/50x50/' + GOOD_IMAGE)
		self.assert_(cr.todo)
		self.assert_(cr.run_commands())

		self.mox.VerifyAll()

	def test_run_commands__thumb_pixel(self):
		self.__mock_s3()

		cr = CommandRunner()
		cr.parse_url('thumb/64/' + GOOD_IMAGE)
		self.assert_(cr.todo)
		self.assert_(cr.run_commands())

		self.mox.VerifyAll()

	def test_run_commands__404(self):
		cr = CommandRunner()
		cr.parse_url('resize/50x50/patrickomatic.com/afdshkfdsa.html')
		self.assert_(cr.todo)

		self.assertRaises(ImageNotFoundException, cr.run_commands)

	def test_run_commands__bad_content_type(self):
		cr = CommandRunner()
		cr.parse_url('resize/50x50/patrickomatic.com/index.html')
		self.assert_(cr.todo)

		self.assertRaises(ImageNotFoundException, cr.run_commands)

	def test_run_commands__image_changed(self):
		image = ModifiedImage.objects.get(id=1)
		image.original_file_hash = 'asfdlj'
		image.last_modified = None
		image.save()

		hash = image.hash

		cr = CommandRunner()
		cr.parse_url(image.get_absolute_url()[1:])
		self.assert_(cr.todo)
		self.assert_(cr.run_commands())

		image = ModifiedImage.objects.get(hash=hash)

	def __mock_s3(self):
		self.mox.StubOutWithMock(boto.s3.key, '__init__')
		boto.s3.key.Key(mox.IgnoreArg())
		self.mox.StubOutWithMock(boto.s3.key.Key, 'set_contents_from_filename')
		boto.s3.key.Key.set_contents_from_filename(mox.IgnoreArg(), mox.IgnoreArg())
		self.mox.ReplayAll()


class ValidatorTest(TestCase):
	def test_validate_percent(self):
		try:
			validate_percent(1)
			validate_percent(2)
			validate_percent(20)
			validate_percent(35)
			validate_percent(90)
			validate_percent(99)
		except ValueError:
			self.fail()
		
	def test_validate_percent__invalid(self):
		self.assertRaises(ValueError, validate_percent, 0)
		self.assertRaises(ValueError, validate_percent, 10000)
		self.assertRaises(ValueError, validate_percent, -50)
		self.assertRaises(ValueError, validate_percent, 1001)


	def test_validate_x_y(self):
		try:
			validate_x_y(1, 1)
			validate_x_y(5, 10)
		except ValueError:
			self.fail()

	def test_validate_x_y__invalid(self):
		self.assertRaises(ValueError, validate_x_y, -1, -1)
		self.assertRaises(ValueError, validate_x_y, 0, -1)
		self.assertRaises(ValueError, validate_x_y, -1, 0)


	def test_validate_width_height(self):
		try:
			validate_width_height(1, 50)
			validate_width_height(20, 1000)
			validate_width_height(1, 5000)
		except ValueError:
			self.fail()

	def test_validate_width_height__invalid(self):
		self.assertRaises(ValueError, validate_width_height, 0, -1)
		self.assertRaises(ValueError, validate_width_height, -1, 20)
		self.assertRaises(ValueError, validate_width_height, 20, 5001)
		self.assertRaises(ValueError, validate_width_height, 5001, 20)


class ImageViewsTest(TestCase):
	def test_modify(self):
		response = self.client.get('/bw/' + GOOD_IMAGE)
		self.assert_(response.status_code == 302)

		response = self.client.get('/square/300/' + GOOD_IMAGE)
		self.assert_(response.status_code == 302)

	def test_modify__unicode_x(self):
		response = self.client.get('/resize/300%C3%97400/' + GOOD_IMAGE)
		self.assert_(response.status_code == 302)

	def test_modify__http(self):
		response = self.client.get('/resize/300%C3%97400/http://' + GOOD_IMAGE)
		self.assert_(response.status_code == 302)

	def test_modify__http_single_slash(self):
		response = self.client.get('/resize/300%C3%97400/http:/' + GOOD_IMAGE)
		self.assert_(response.status_code == 302)

	def test_modify__site_exists(self):
		site = Site(domain_name='patrickomatic.com')
		site.save()

		response = self.client.get('/square/300/' + GOOD_IMAGE)
		self.assert_(response.status_code == 302)

	def test_modify__over_quota(self):
		site = Site(domain_name='patrickomatic.com')
		site.usage = 60 * 1024 * 1024 * 1024
		site.save()

		response = self.client.get('/square/300/' + GOOD_IMAGE)
		self.assertRedirects(response, 'http://urlimg.com/media/over_quota.png')

	def test_modify__suspended(self):
		site = Site(domain_name='patrickomatic.com')
		site.disabled = True
		site.save()

		response = self.client.get('/square/300/' + GOOD_IMAGE)
		self.assertRedirects(response, 'http://urlimg.com/media/suspended.png')

	def test_modify__image_404(self):
		response = self.client.get('/square/300/patrickomatic.com/foo.jpg')
		self.assert_(response.status_code == 404)


class ImageModelsTest(TestCase):
	def test_domain_name(self):
		self.assert_('patrickomatic.com' == domain_name('patrickomatic.com'))
		self.assert_('www.patrickomatic.com' == domain_name('www.patrickomatic.com/'))
		self.assert_('www.patrickomatic.com' == domain_name('http://www.patrickomatic.com/'))
		self.assert_('www.patrickomatic.com' == domain_name('http:/www.PATRICKOMATIC.com/'))
		self.assert_('www.patrickomatic.com' == domain_name('http://www.patrickomatic.com/a bunch of stuff'))
		self.assert_('images.patrickomatic.com' == domain_name('http://images.patrickomatic.com/'))

	def test_readable_bytes(self):
		self.assert_('0 KB' == readable_bytes(1))
		self.assert_('0 KB' == readable_bytes(100))
		self.assert_('0 KB' == readable_bytes(1023))
		self.assert_('1.00 KB' == readable_bytes(1024))
		self.assert_('2.00 KB' == readable_bytes(2048))
		self.assert_('2.50 KB' == readable_bytes(2560))
		self.assert_('1.00 MB' == readable_bytes(1024 * 1024))
		self.assert_('3.00 MB' == readable_bytes(3 * 1024 * 1024))
		self.assert_('1.00 GB' == readable_bytes(1024 * 1024 * 1024))
		self.assert_('3.00 GB' == readable_bytes(3 * 1024 * 1024 * 1024))
		self.assert_('1.00 TB' == readable_bytes(1024 * 1024 * 1024 * 1024))
		self.assert_('3.00 TB' == readable_bytes(3 * 1024 * 1024 * 1024 * 1024))
		self.assert_('1024.00 TB' == readable_bytes(1024 * 1024 * 1024 * 1024 * 1024))
		self.assert_('3072.00 TB' == readable_bytes(3 * 1024 * 1024 * 1024 * 1024 * 1024))

	def test_url_path(self):
		self.assert_('/foo/poo/foo.jpg' == url_path('http://google.com/foo/poo/foo.jpg'))
		self.assert_('/foo/poo/Foo.jpg' == url_path('http://www.google.com/foo/poo/Foo.jpg'))
		self.assert_('/foo/poo/foo.jpg' == url_path('google.com/foo/poo/foo.jpg'))

	def test_sanitize_url(self):
		self.assert_(sanitize_url('patrickomatic.com/foo.jpg') == 'http://patrickomatic.com/foo.jpg')
		self.assert_(sanitize_url('http://patrickomatic.com/foo.jpg') == 'http://patrickomatic.com/foo.jpg')
		self.assert_(sanitize_url('www.patrickomatic.com/foo.jpg') == 'http://www.patrickomatic.com/foo.jpg')
		self.assert_(sanitize_url('http:/www.patrickomatic.com/foo.jpg') == 'http://www.patrickomatic.com/foo.jpg')

	def test_sanitize_url__quote_space(self):
		self.assert_(sanitize_url('patrickomatic.com/foo poo.jpg') == 'http://patrickomatic.com/foo%20poo.jpg')
		self.assert_(sanitize_url('http://patrickomatic.com/foo poo.jpg') == 'http://patrickomatic.com/foo%20poo.jpg')
		self.assert_(sanitize_url('http:/www.patrickomatic.com/foo poo.jpg') == 'http://www.patrickomatic.com/foo%20poo.jpg')

	def test_valid_image_path(self):
		self.assert_(valid_image_path('patrickomatic.com/foo.jpg'))
		self.assert_(valid_image_path('http://patrickomatic.com/foo.jpg'))
		self.assert_(valid_image_path('http://www.patrickomatic.com/foo.jpg'))
		self.assert_(valid_image_path('www.patrickomatic.com/foo.jpg'))
		self.assert_(valid_image_path('http://www.patrickomatic.com/poo/foo.jpg'))
		self.assert_(valid_image_path('http:/www.patrickomatic.com/poo/foo.jpg'))

	def test_valid_image_path__invalid(self):
		self.assert_(not valid_image_path('http://patrickomatic.com/'))
		self.assert_(not valid_image_path('a.jpg'))
		self.assert_(not valid_image_path('foo/a.jpg'))


	def test_retry(self):
		times_called = [0]

		@retry(5, ValueError)
		def retry_tester():
			times_called[0] += 1
			raise ValueError("success")

		self.assertRaises(ValueError, retry_tester)
		self.assert_(times_called[0] == 5)

	def test_retry__eventually_succeed(self):
		times_called = [0]

		@retry(5, Exception)
		def retry_tester():
			times_called[0] += 1
			if times_called[0] < 3:
				raise Exception

			return "success"

		self.assert_("success" == retry_tester())
		self.assert_(times_called[0] == 3)


class ModifiedImageTest(TestCase):
	fixtures = ['image']

	def setUp(self):
		self.image = ModifiedImage.objects.get(id=1)
		self.image.site = Site.objects.get(domain_name='patrickomatic.com')
		self.mox = mox.Mox()

	def tearDown(self):
		self.mox.UnsetStubs()

	
	def test_save(self):
		ModifiedImage(hash='xxx', original_location='/xxx.jpg', operations='resize/50x50', size=500, site=self.image.site).save()

		self.assert_(ModifiedImage.objects.get(hash='xxx'))

	def test_refresh(self):
		last_id = self.image.id
		self.assert_(self.image.refresh())
		self.assert_(self.image.id != last_id)


	def test_delete(self):
		self.mox.StubOutWithMock(boto.s3.key, '__init__')
		boto.s3.key.Key(mox.IgnoreArg())
		self.mox.StubOutWithMock(boto.s3.key.Key, 'delete')
		boto.s3.key.Key.delete()
		self.mox.StubOutWithMock(boto.s3.key.Key, 'close')
		boto.s3.key.Key.close()
		self.mox.ReplayAll()

		id = self.image.id
		self.image.delete()

		self.assertRaises(ModifiedImage.DoesNotExist, ModifiedImage.objects.get, id=id)
				
		self.mox.VerifyAll()


	def test_get_thumbnail_url(self):
		self.assert_(re.match(r'/%sinternalthumb/\w+/%s%s' \
				% (self.image.operations, self.image.site.domain_name, self.image.original_location),
				self.image.get_thumbnail_url()))


	def test_get_account_url(self):
		self.assertEquals('/account/sites/patrickomatic.com/images/1/', self.image.get_account_url())


	def test_get_absolute_url(self):
		self.assertEquals('/' + self.image.operations + self.image.site.domain_name \
				+ self.image.original_location, self.image.get_absolute_url())

class ImageModuleTest(TestCase):
	def test_color_to_rgb(self):
		self.assert_(color_to_rgb('red') == (255, 0, 0))
		self.assert_(color_to_rgb('green') == (0, 128, 0))
		self.assert_(color_to_rgb('foo') == None)

	def test_hex_to_decimal(self):
		self.assert_(hex_to_decimal('FF') == 255)
		self.assert_(hex_to_decimal('0') == 0)
		self.assert_(hex_to_decimal('CC') == 204)

	
	def test_hex_to_rgb(self):
		self.assert_(hex_to_rgb('#FF00CC') == (255, 0, 204))
		self.assert_(hex_to_rgb('000080') == (0, 0, 128))
		self.assert_(hex_to_rgb('0CF') == (0, 204, 255))
		self.assert_(hex_to_rgb('#0CF') == (0, 204, 255))
		self.assert_(hex_to_rgb('#fooooooo') == None)
