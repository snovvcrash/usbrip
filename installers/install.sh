#!/usr/bin/env bash

: '
%file install.sh
%author Sam Freeside (@snovvcrash) <snovvcrash@protonmail[.]ch>
%date 2018-05-28

%brief usbrip installer.

%license
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
%endlicense
'

# Usage: sudo -H ./install.sh

shopt -s expand_aliases

# ----------------------- Constants ------------------------

OPT="/opt/usbrip"
LOG="/var/opt/usbrip/log"
STORAGE="/var/opt/usbrip/storage"
SYMLINK="/usr/local/bin/usbrip"

W="\033[1;37m"  # WHITE
G="\033[1;32m"  # GREEN
R="\033[1;31m"  # RED
NC="\033[0m"    # NO COLOR

# --------------------- usbrip aliases ---------------------

alias createHistoryStorage="${OPT}/venv/bin/usbrip storage create history -e"

alias generateAuthorizedDeviceList="${OPT}/venv/bin/usbrip events gen_auth /var/opt/usbrip/trusted/auth.json -e -a vid pid"

alias createViolationsStorage="${OPT}/venv/bin/usbrip storage create violations -i /var/opt/usbrip/trusted/auth.json -e -a vid pid"

# --------------- Check for root privileges ----------------

if [[ $EUID -ne 0 ]]; then
	/usr/bin/printf "${R}>>>>${NC} Please run as root:\nsudo -H %s\n" "${0}"
	exit 1
fi

# -------------------- Handle switches ---------------------

if [[ "$1" == "-s" ]] || [[ "$1" == "--storages" ]]; then
	STORAGES=true
else
	STORAGES=false
fi

# -------------- Check for required packages ---------------

# virtualenv

if ! /usr/bin/virtualenv --version > /dev/null; then
	/usr/bin/printf "${R}>>>>${NC} Unresolved dependency: virtualenv. To install this package run:\n%s\n" \
                    "sudo apt install python-virtualenv virtualenv"
	exit 1
fi

# p7zip-full

if ! /usr/bin/dpkg-query -W -f='${Status}' p7zip-full | /bin/grep "ok installed" > /dev/null; then
	/usr/bin/printf "${R}>>>>${NC} Unresolved dependency: p7zip-full. To install this package run:\n%s\n" \
                    "sudo apt install p7zip-full"
	exit 1
fi

# ------------------- Create directories -------------------

# OPT

/usr/bin/printf "${W}>>>>${NC} Creating directory: '${OPT}'\n"

if [[ -d "${OPT}" ]]; then
	/usr/bin/printf "${R}>>>>${NC} ${OPT} already exists. First run:\n%s\n" \
                    "sudo uninstall.sh --all"
	exit 1
fi

if /bin/mkdir "${OPT}"; then
	/usr/bin/printf "${G}>>>>${NC} Successfully created directory: '${OPT}'\n\n"
else
	/usr/bin/printf "${R}>>>>${NC} Failed to create directory: '${OPT}'\n"
	exit 1
fi

# LOG

/usr/bin/printf "${W}>>>>${NC} Creating directory: '${LOG}'\n"

if [[ -d "${LOG}" ]]; then
	/usr/bin/printf "${R}>>>>${NC} ${LOG} already exists. First run:\n%s\n" \
                    "sudo uninstall.sh --all"
	exit 1
fi

if /bin/mkdir -p "${LOG}"; then
	/usr/bin/printf "${G}>>>>${NC} Successfully created directory: '${LOG}'\n\n"
else
	/usr/bin/printf "${R}>>>>${NC} Failed to create directory: '${LOG}'\n"
	exit 1
fi

# STORAGE

/usr/bin/printf "${W}>>>>${NC} Creating directory: '${STORAGE}'\n"

if [[ -d "${STORAGE}" ]]; then
	/usr/bin/printf "${R}>>>>${NC} ${STORAGE} already exists. First run:\n%s\n" \
                    "sudo uninstall.sh --all"
	exit 1
fi

if /bin/mkdir -p "${STORAGE}"; then
	/usr/bin/printf "${G}>>>>${NC} Successfully created directory: '${STORAGE}'\n\n"
else
	/usr/bin/printf "${R}>>>>${NC} Failed to create directory: '${STORAGE}'\n"
	exit 1
fi

# ------------ Build python virtual environment ------------

/usr/bin/printf "\n"
/usr/bin/printf "${W}>>>>${NC} Building python virtual environment\n"

if /usr/bin/virtualenv -p /usr/bin/python3 "${OPT}/venv"; then
	/usr/bin/printf "${G}>>>>${NC} Successfully builded python virtual environment\n\n"
else
	/usr/bin/printf "${R}>>>>${NC} Failed to build python virtual environment\n"
	exit 1
fi

# --------------------- PIP Install . ----------------------

/usr/bin/printf "${W}>>>>${NC} (PIP-)Installing usbrip\n"

if "${OPT}/venv/bin/pip" install "${PWD}"; then
	/usr/bin/printf "${G}>>>>${NC} Successfully (PIP-)installed usbrip\n\n"
else
	/usr/bin/printf "${R}>>>>${NC} Failed to (PIP-)install usbrip\n"
	exit 1
fi

# --------------------- Create symlink ---------------------

if [[ -e "${SYMLINK}" ]]; then
	/bin/rm "${SYMLINK}"
fi

if /bin/ln -s "${OPT}/venv/bin/usbrip" "${SYMLINK}"; then
	/usr/bin/printf "${G}>>>>${NC} Created symlink: '${SYMLINK}'\n"
fi

# ----------------- Create usbrip storages -----------------

if $STORAGES; then
	# History

	/usr/bin/printf "${W}>>>>${NC} Creating usbrip history storage\n"

	if createHistoryStorage; then
		/usr/bin/printf "${G}>>>>${NC} Successfully created usbrip history storage\n\n"
	else
		/usr/bin/printf "${R}>>>>${NC} Failed to create usbrip history storage\n"
		exit 1
	fi

	# Gen Auth

	/usr/bin/printf "${W}>>>>${NC} Generating authorized device list\n"

	if generateAuthorizedDeviceList; then
		/usr/bin/printf "${G}>>>>${NC} Successfully generated authorized device list\n\n"
	else
		/usr/bin/printf "${R}>>>>${NC} Failed to generate authorized device list\n"
		exit 1
	fi

	# Violations

	/usr/bin/printf "${W}>>>>${NC} Creating usbrip violations storage\n"

	if createViolationsStorage; then
		/usr/bin/printf "${G}>>>>${NC} Successfully created usbrip violations storage\n\n"
	else
		/usr/bin/printf "${R}>>>>${NC} Failed to create usbrip violations storage\n"
		exit 1
	fi
fi

# -------------------------- Done --------------------------

/usr/bin/printf "${G}>>>>${NC} Done.\n"
