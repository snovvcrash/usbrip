#!/usr/bin/env bash

: '
@file uninstall.sh
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-05

@brief usbrip uninstaller.

@license
Copyright (W) 2018 Sam Freeside

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
@endlicense
'

# Usage:
# sudo ./uninstall.sh [--all]

# ----------------------- Constants ------------------------

OPT="/opt/usbrip"
VAR_OPT="/var/opt/usbrip"
SYMLINK="/usr/local/bin/usbrip"

G="\033[1;32m"  # GREEN
R="\033[1;31m"  # RED
NC="\033[0m"    # NO COLOR

# --------------- Check for root privileges ----------------

if [[ $EUID -ne 0 ]]; then
	printf "${R}>>>>${NC} Please run as root:\nsudo -H %s\n" "${0}"
	exit 1
fi

# -------------------- Handle switches ---------------------

if [[ "$1" == "--all" ]]; then
	ALL=true
else
	ALL=false
fi

# ------------------- Remove directories -------------------

# OPT

if rm -r "${OPT}" 2> /dev/null; then
	printf "${G}>>>>${NC} Removed directory: '${OPT}'\n"
fi

# VAR_OPT

if $ALL; then
	if rm -r "${VAR_OPT}" 2> /dev/null; then
		printf "${G}>>>>${NC} Removed directory: '${VAR_OPT}'\n"
	fi
fi

# SYMLINK

if rm "${SYMLINK}" 2> /dev/null; then
	printf "${G}>>>>${NC} Removed symlink: '${SYMLINK}'\n"
fi

# -------------------------- Done --------------------------

printf "\n"
printf "${G}>>>>${NC} Done.\n"
