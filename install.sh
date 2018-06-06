#!/usr/bin/env bash

: '
@file install.sh
@author Sam Freeside <snovvcrash@protonmail.com>
@date 2018-05

@brief usbrip installer.

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
# sudo -H ./install.sh

shopt -s expand_aliases

# --------------------- usbrip aliases ---------------------

alias createHistoryStorage="usbrip storage create history -e"

alias generateAuthorizedDeviceList="usbrip events gen_auth /var/opt/usbrip/trusted/auth.json -e -a vid pid"

alias createViolationsStorage="usbrip storage create violations -i /var/opt/usbrip/trusted/auth.json -e -a vid pid"

# ----------------------- Constants ------------------------

OPT="/opt/usbrip"
LOG="/var/opt/usbrip/log"
STORAGE="/var/opt/usbrip/storage"
SYMLINK="/usr/local/bin/usbrip"

W="\033[1;37m"  # WHITE
G="\033[1;32m"  # GREEN
R="\033[1;31m"  # RED
NC="\033[0m"    # NO COLOR

# --------------- Check for root privileges ----------------

if [[ $EUID -ne 0 ]]; then
	printf "${R}>>>>${NC} Please run as root:\nsudo -H %s\n" "${0}"
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

if ! virtualenv --version > /dev/null; then
	printf "${R}>>>>${NC} Unresolved dependency: virtualenv. To install this package run:\n%s\n" \
           "sudo apt install python-virtualenv virtualenv"
	exit 1
fi

# p7zip-full

if ! dpkg-query -W -f='${Status}' p7zip-full | grep "ok installed" > /dev/null; then
	printf "${R}>>>>${NC} Unresolved dependency: p7zip-full. To install this package run:\n%s\n" \
           "sudo apt install p7zip-full"
	exit 1
fi

# ------------------- Create directories -------------------

# OPT

printf "${W}>>>>${NC} Creating directory: '${OPT}'\n"

if [[ -d "${OPT}" ]]; then
	printf "${R}>>>>${NC} ${OPT} already exists. First run:\n%s\n" \
           "sudo uninstall.sh --all"
	exit 1
fi

if mkdir "${OPT}"; then
	printf "${G}>>>>${NC} Successfully created directory: '${OPT}'\n\n"
else
	printf "${R}>>>>${NC} Failed to create directory: '${OPT}'\n"
	exit 1
fi

# LOG

printf "${W}>>>>${NC} Creating directory: '${LOG}'\n"

if [[ -d "${LOG}" ]]; then
	printf "${R}>>>>${NC} ${LOG} already exists. First run:\n%s\n" \
           "sudo uninstall.sh --all"
	exit 1
fi

if mkdir -p "${LOG}"; then
	printf "${G}>>>>${NC} Successfully created directory: '${LOG}'\n\n"
else
	printf "${R}>>>>${NC} Failed to create directory: '${LOG}'\n"
	exit 1
fi

# STORAGE

printf "${W}>>>>${NC} Creating directory: '${STORAGE}'\n"

if [[ -d "${STORAGE}" ]]; then
	printf "${R}>>>>${NC} ${STORAGE} already exists. First run:\n%s\n" \
           "sudo uninstall.sh --all"
	exit 1
fi

if mkdir -p "${STORAGE}"; then
	printf "${G}>>>>${NC} Successfully created directory: '${STORAGE}'\n\n"
else
	printf "${R}>>>>${NC} Failed to create directory: '${STORAGE}'\n"
	exit 1
fi

# ----------------- Chmod, copy & symlink ------------------

# Chmod

if chmod +x usbrip.py; then
	printf "${G}>>>>${NC} Changed mode (+x) for usbrip.py\n"
fi

# Copy

if cp -r --no-preserve=ownership * "${OPT}"; then
	printf "${G}>>>>${NC} Copied current folder's contents to ${OPT}\n"
fi

# Symlink

if [[ -e "${SYMLINK}" ]]; then
	rm "${SYMLINK}"
fi

if ln -s "${OPT}/usbrip.py" "${SYMLINK}"; then
	printf "${G}>>>>${NC} Created symlink: '${SYMLINK}'\n"
fi

# ------------ Build python virtual environment ------------

printf "\n"
printf "${W}>>>>${NC} Building python virtual environment\n"

if virtualenv -p python3 "${OPT}/venv"; then
	printf "${G}>>>>${NC} Successfully builded python virtual environment\n\n"
else
	printf "${R}>>>>${NC} Failed to build python virtual environment\n"
	exit 1
fi

# ---------------- Install PIP requirements ----------------

printf "${W}>>>>${NC} Installing PIP requirements\n"

if "${OPT}/venv/bin/pip" install -r requirements.txt; then
	printf "${G}>>>>${NC} Successfully installed PIP requirements\n\n"
else
	printf "${R}>>>>${NC} Failed to install PIP requirements\n"
	exit 1
fi

# ----------------- Create usbrip storages -----------------

if $STORAGES; then
	# History

	printf "${W}>>>>${NC} Creating usbrip history storage\n"

	if createHistoryStorage; then
		printf "${G}>>>>${NC} Successfully created usbrip history storage\n\n"
	else
		printf "${R}>>>>${NC} Failed to create usbrip history storage\n"
		exit 1
	fi

	# Gen Auth

	printf "${W}>>>>${NC} Generating authorized device list\n"

	if generateAuthorizedDeviceList; then
		printf "${G}>>>>${NC} Successfully generated authorized device list\n\n"
	else
		printf "${R}>>>>${NC} Failed to generate authorized device list\n"
		exit 1
	fi

	# Violations

	printf "${W}>>>>${NC} Creating usbrip violations storage\n"

	if createViolationsStorage; then
		printf "${G}>>>>${NC} Successfully created usbrip violations storage\n\n"
	else
		printf "${R}>>>>${NC} Failed to create usbrip violations storage\n"
		exit 1
	fi
fi

# -------------------------- Done --------------------------

printf "${G}>>>>${NC} Done.\n"
