#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LICENSE

Copyright (C) 2018 Sam Freeside

This file is part of usbrip.

usbrip is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

usbrip is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with usbrip.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = 'Sam Freeside (@snovvcrash)'
__email__  = 'snovvcrash@protonmail[.]ch'

__license__ = 'GPL-3.0'
__date__    = '2018-03-21'
__version__ = '2.1'
__site__    = 'https://github.com/snovvcrash/usbrip'
__brief__   = 'USB device artifacts tracker.'


import glob
import shutil
import os

from setuptools import setup, find_packages, Command


class CleanCommand(Command):
	"""Custom clean command to tidy up the project root."""
	CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info'.split(' ')

	user_options = []

	def initialize_options(self):
		pass

	def finalize_options(self):
		pass

	def run(self):
		here = os.path.abspath(os.path.dirname(__file__))

		for path_spec in self.CLEAN_FILES:
			abs_paths = glob.glob(os.path.normpath(os.path.join(here, path_spec)))
			for path in abs_paths:
				if not path.startswith(here):
					# Die if path in CLEAN_FILES is absolute + outside this directory
					raise ValueError(f'{path} is not a path inside {here}')
				print(f'removing {os.path.relpath(path)}')
				shutil.rmtree(path)


def parse_requirements(file):
	required = []
	with open(file, 'r') as f:
		for req in f:
			if not req.strip().startswith('#'):
				required.append(req)

	return required


long_description = '''
Simple command line forensics tool for tracking\
USB device artifacts (history of USB events)\
on GNU/Linux.\
'''

keywords = 'forensics cybersecurity infosec usb-history usb-devices'

setup(
	name='usbrip',
	version=__version__,
	url=__site__,
	author=__author__,
	author_email=__email__,
	license=__license__,
	description=__brief__,
	long_description=long_description,
	keywords=keywords,
	packages=find_packages(),

	data_files=[
		('', ['README.rst', 'requirements.txt', 'usbrip.cron']),
		('usbrip/usb_ids', ['usbrip/usb_ids/usb.ids'])
	],

	python_requires='>=3.6',
	install_requires=parse_requirements('requirements.txt'),

	entry_points={
		'console_scripts': [
			'usbrip=usbrip.usbrip:main'
		],
	},

	cmdclass={
        'clean': CleanCommand,
    },

	zip_safe=False
)
