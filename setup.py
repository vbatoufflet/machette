#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Append base directory to the PYTHONPATH
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

# Import needed modules
import distutils.cmd
from distutils.command.build import build as _build
from distutils.command.clean import clean as _clean
from distutils.command.install_data import install_data as _install_data
from distutils.command.install_lib import install_lib as _install_lib
from distutils.core import setup
from regextool import __author__, __email__, __fullname__, __license__, __shortname__, __version__, __website__

class build(_build):
	"""
	Build distribution.
	"""

	sub_commands = _build.sub_commands + [
		( 'gendoc', None ),
		( 'genlocale', None ),
	]

	def run(self):
		# Continue with distutils built-in build command
		return _build.run(self)

class clean(_clean):
	"""
	Remove various created files.
	"""

	__targets = [
		'doc/%s.1' % __shortname__,
		'locale',
		'MANIFEST',
		'%s/*.pyc' % __shortname__,
	]

	def run(self):
		import glob, shutil

		# Cleanup files
		for target in clean.__targets:
			for path in glob.glob(target):
				if os.path.isdir(path):
					print("removing '%s' directory" % path)
					shutil.rmtree(path)
				elif os.path.isfile(path):
					print("removing '%s' file" % path)
					os.unlink(path)

		# Continue with distutils built-in clean command
		return _clean.run(self)

class gendoc(distutils.cmd.Command):
	"""
	Generate documentation files.
	"""

	description = 'generate documentation files'
	user_options = list()

	def finalize_options(self):
		pass

	def initialize_options(self):
		pass

	def run(self):
		if self and self.dry_run:
			return
		
		# Generate manpage
		from docutils.core import publish_file
		from docutils.writers.manpage import Writer

		print('generating manpages')

		publish_file(
			writer=Writer(),
			source_path=os.path.join('doc', __shortname__ + '.1.rst'),
			destination_path=os.path.join('doc', __shortname__ + '.1'),
		)

class genlocale(distutils.cmd.Command):
	"""
	Generate locale .mo catalog files.
	"""

	description = 'build locale .mo catalogs'
	user_options = list()

	def finalize_options(self):
		pass

	def initialize_options(self):
		pass

	def run(self):
		if self and self.dry_run:
			return

		# Generate .mo catalog files
		for pofile in os.listdir('po'):
			lang, ext = os.path.splitext(pofile)

			# Skip non .po files
			if ext != '.po':
				continue

			# Get .mo file path
			mofile = os.path.join('locale', lang, 'LC_MESSAGES', __shortname__ + '.mo')

			if not os.path.exists(os.path.dirname(mofile)):
				os.makedirs(os.path.dirname(mofile))
			
			# Generate .mo file
			print('generating ' + mofile)
			os.system('msgfmt -o %s %s' % (mofile, os.path.join('po', '%s.po' % lang)))

class install_data(_install_data):
	"""
	Install data files.
	"""

	def run(self):
		# Install locale .mo catalog files
		for lang in os.listdir('locale'):
			self.data_files.append(( 'share/locale/%s/LC_MESSAGES' % lang,  [ 'locale/%s/LC_MESSAGES/%s.mo' % (lang, __shortname__) ] ))

		# Install manpage
		self.data_files.append(( 'share/man/man1', [ 'doc/%s.1' % __shortname__ ] ))

		# Continue with distutils built-in install_data command
		return _install_data.run(self)

class install_lib(_install_lib):
	"""
	Install library files.
	"""

	def run(self):
		# Get installation prefix
		root = self.distribution.get_command_obj('install').root
		prefix = self.distribution.get_command_obj('install').install_data

		if root and prefix:
			prefix = os.path.abspath(prefix).replace(os.path.abspath(root), '')

		# Update paths
		pathfile = os.path.join(self.build_dir, __shortname__, 'path.py')

		# Load file data
		fd = open(pathfile, 'r')
		data = fd.read()

		# Replace paths
		print("updating '%s' paths" % pathfile)

		data = data.replace(
			'DATA_DIR = get_source_directory()',
			'DATA_DIR = %s' % repr(os.path.join(prefix, 'share', __shortname__)),
		)

		data = data.replace(
			"LOCALE_DIR = get_source_directory('locale')",
			'LOCALE_DIR = %s' % repr(os.path.join(prefix, 'share', 'locale')),
		)

		# Write modifications and close file
		fd = open(pathfile, 'w')
		fd.write(data)
		fd.close()

		# Continue with distutils built-in install_lib command
		return _install_lib.run(self)

# Define setup meta-data
setup(
	name=__shortname__,
	version=__version__,
	description=__fullname__,
	author=__author__,
	author_email=__email__,
	url=__website__,
	license=__license__,
	cmdclass={
		'build': build,
		'clean': clean,
		'gendoc': gendoc,
		'genlocale': genlocale,
		'install_data': install_data,
		'install_lib': install_lib,
	},
	scripts=[
		'bin/' + __shortname__,
	],
	packages=[
		'regextool',
	],
	data_files=[
		( 'share/' + __shortname__, [ 'AUTHORS', 'ChangeLog', 'LICENSE', 'README', 'TRANSLATORS' ] ),
		( 'share/' + __shortname__ + '/ui', [ 'ui/main.ui', 'ui/pref.ui' ] ),
	],
)
