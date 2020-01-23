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

__author__ = 'Sam Freeside (@snovvcrash)'
__email__  = 'snovvcrash@protonmail[.]ch'
__site__   = 'https://github.com/snovvcrash/usbrip'
__brief__  = 'Configuration file parser'

import os
import stat
from configparser import ConfigParser

from usbrip.lib.core.common import CONFIG_FILE
from usbrip.lib.core.common import print_info
from usbrip.lib.core.common import print_warning


def get_config_parser():
	config_parser = ConfigParser(allow_no_value=True)
	config_parser.optionxform = str

	os.makedirs(CONFIG_FILE.rsplit('/', 1)[0], exist_ok=True)

	if os.path.isfile(CONFIG_FILE):
		config_parser.read(CONFIG_FILE, encoding='utf-8')
		print_info(f'Configuration loaded: "{CONFIG_FILE}"')

	else:
		print_warning('No configuration file found, creating new one...')

		config_parser.add_section('history')
		config_parser.set('history', 'password', 'R1pp3r!')

		config_parser.add_section('violations')
		config_parser.set('violations', 'password', 'R1pp3r!')

		print_info(f'New configuration file: "{CONFIG_FILE}"')

		with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
			config_parser.write(f)

		os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 600

	return config_parser
