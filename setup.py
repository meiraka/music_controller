"""
================================
setup script for MusicController
================================

Requirements
============

* wxPython 2.8 or later
* python-mpd
* pynotify (optional)
* gntp (optional)

Build or Install
================

Build .app for Mac OSX:
	python setup.py py2app

Build .deb for debian or Ubuntu:
	python setup.py debian

Install as a python package:
	python setup.py install

"""
import os
import sys
import glob
import subprocess
import setuptools
import re
sys.path.append(os.getcwdu()+'/src')
import version

def get_command_out(command):
	try:
		return subprocess.check_output(command.split(' '))[:-1]
	except:
		return ''

def get_rev():
	""" Returns git rev."""
	import commands
	import re
	out = len([i for i in get_command_out('git log').split('\n') if i.startswith('commit ')])
	if out:
		return str(out)
	else:
		return ''

def test():
	sys.path.append(os.path.abspath('src/common/'))
	sys.path.append(os.path.abspath('tests'))
	import unittest
	import client_test
	classes = [getattr(client_test,i) for i in dir(client_test) if i.startswith('Test')]
	for i in classes:
		s = unittest.makeSuite(i)
		unittest.TextTestRunner(verbosity=2).run(s)

class BuildInfo(object):
	def __enter__(self):
		try:
			self.generate_build_info()
		except:
			pass

	def __exit__(self,*args):
		try:
			self.delete_build_info()
		except:
			pass

	def generate_build_info(self):
		""" save Builder information."""
		data = dict(
			user = get_command_out('whoami'),
			host = get_command_out('hostname'),
			revision = get_rev()
			)
		build_info = '\n'.join(['%s = "%s"' % (k,v) for k,v in data.iteritems()])
		print build_info
		f = open('src/buildinfo.py','w')
		f.write(build_info)

	def delete_build_info(self):
		os.remove('src/buildinfo.py')
		return False

class Setup(object):
	def __init__(self):
		""" Sets package name, install dir and require packages
		 for setuptools.setup() arg.
		"""
		self.setup_args = {}
		self.setup_args['packages'] = ['MusicController']
		self.setup_args['package_dir'] = {'MusicController':'src'}
		self.setup_args['package_data'] = {'MusicController':['common/*']}
		self.setup_args['data_files'] = [
						('bin',['music-controller']),
						('share/applications',['unix/music-controller.desktop'])
						]
		self.setup_args['setup_requires'] = ['python-mpd']
		self.add_locales()

	def add_locales(self):
		langs = glob.glob('locale/*')
		for lang in langs:
			self.setup_args['data_files'].append(
				('share/'+lang+'/LC_MESSAGES',glob.glob(lang+'/LC_MESSAGES/*.mo'))
				)

	def generate_documents(self):
		""" Generates man pages and sets value for setuptools.setup() arg.

		Sets:
			- man page install dir.
		"""
		# man pages
		filename = 'music-controller.rst'
		docs = ['man/'+filename]
		docs = docs + glob.glob('man/*/'+filename)
		section = '1'
		from docutils.core import publish_string
		from docutils.writers import manpage
		import gzip
		re_version  = re.compile(':Version:[^\n]+')
		app_version = version.__version__
		rev = get_rev()
		if rev:
			app_version + '.' + rev
		for rstfile in docs:
			f = open(rstfile)
			rst = f.read()
			f.close()
			rst = re_version.sub(':Version: '+app_version,rst)
			man = publish_string(rst,writer=manpage.Writer())
			manfile = rstfile.replace('rst',section+'.gz')
			with gzip.open(manfile,'wb') as f:
				f.write(man)
			lang_dir = rstfile.replace('man/','').replace(filename,'')
			mandir = 'share/man/'+lang_dir+'man1'
			self.setup_args['data_files'].append(
					(mandir,[manfile])
					)
		
		

	def py2app(self):
		""" Generates PList settings and sets values for setuptools.setup() arg.

		Sets:
			- execute script
			- require package
			- plist file
			- app icon.(not yet)
		"""
		from plistlib import Plist
		self.setup_args['app'] = ['src/__main__.py']
		self.setup_args['setup_requires'].append('py2app')
		plist = Plist.fromFile('osx/Info.plist')
		plist.update ( dict(
				CFBundleShortVersionString = version.__version__+':'+get_rev(),
				NSHumanReadableCopyright = u"Copyright 2012 mei raka",
				))
		if not 'options' in self.setup_args:
			self.setup_args['options'] = {}
		if not 'py2app' in self.setup_args['options']:
			self.setup_args['options']['py2app'] = {}
		self.setup_args['options']['py2app'] = dict(
				plist=plist
				)

		# add lang
		'''
		# comment out because Help menu can not have search item in Japanese,
		# disable i18n in Mac.
		langs = glob.glob('osx/*.lproj')
		for lang in langs:
			self.setup_args['data_files'].append(
				(os.path.basename(lang),glob.glob(lang+'/*'))
				)
		'''


	def run(self):
		""" Builds or installs app.

		Before setup, generates buildinfo.py.
		"""
		try:
			self.generate_documents()
		except:
			pass
		if 'py2app' in sys.argv:
			self.py2app()
		setuptools.setup(name='MusicController',
			version=version.__version__,
			author='mei raka',
			**self.setup_args)


if __name__ == '__main__':
	if 'debian' in sys.argv:
		with BuildInfo():
			os.system('debuild -us -uc -I')
	elif not 'test' in sys.argv:
		with BuildInfo():
			builder = Setup()
			builder.run()
	else:
		test()
