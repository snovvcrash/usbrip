#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LICENSE

Copyright (C) 2020 Sam Freeside

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

__author__  = 'Sam Freeside (@snovvcrash)'
__email__   = 'snovvcrash@protonmail.ch'
__license__ = 'GPL-3.0'
__site__    = 'https://github.com/snovvcrash/usbrip'
__brief__   = 'USB device artifacts tracker'

import glob
import shutil
import sys
import os
from subprocess import check_output

from setuptools import setup, find_packages, Command
from setuptools.command.install import install

from usbrip import __version__


class LocalInstallCommand(install):
	"""Custom install command to install local Python dependencies."""
	def run(self):
		install.run(self)
		tools_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '3rdPartyTools')

		deps = []
		for dep in os.listdir(tools_dir):
			if dep.startswith('wheel-'):
				wheel = dep
			else:
				deps.append(dep)

		resolve(wheel, tools_dir)

		for dep in deps:
			resolve(dep, tools_dir)


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
				print(f'[*] Removing {os.path.relpath(path)}')
				shutil.rmtree(path)


def resolve(dep, path=None):
		pip = os.path.join(sys.executable.rsplit('/', 1)[0], 'pip')

		if path:
			args = [pip, 'install', os.path.join(path, dep)]
			dep_type = 'local'
		else:
			args = [pip, 'install', dep]
			dep_type = 'remote'

		if 'Successfully installed' in check_output(args).decode('utf-8'):
			print(f'[*] Resolved ({dep_type}) dependency: {dep}')


def parse_requirements(file):
	required = []
	with open(file, 'r') as f:
		for req in f:
			if not req.strip().startswith('#'):
				required.append(req)

	return required


long_description = '''\
	Simple CLI forensics tool for tracking \
	USB device artifacts (history of USB events) \
	on GNU/Linux.\
'''.replace('\t', '')

keywords = 'forensics cybersecurity infosec usb-history usb-devices'

resolve('wheel')

setup(
	name='usbrip',
	version=__version__,
	url=__site__,
	author=__author__,
	author_email=__email__,
	license=__license__,
	description=__brief__,
	long_description=long_description,
	long_description_content_type='text/markdown',
	keywords=keywords,
	packages=find_packages(),
	zip_safe=False,

	python_requires='>=3.6',
	install_requires=parse_requirements('requirements.txt'),

	data_files=[
		('', ['README.md', 'requirements.txt'])
	],

	cmdclass={
		'install': LocalInstallCommand,
		'clean': CleanCommand
	},

	entry_points={
		'console_scripts': [
			'usbrip=usbrip.__main__:main'
		]
	}
)
