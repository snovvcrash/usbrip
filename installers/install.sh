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

# Usage: sudo -H ./install.sh [-l/--local] [-s/--storages]

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
	/usr/bin/printf "${R}[!]${NC} Please run as root:\nsudo -H %s\n" "${0}"
	exit 1
fi

# -------------------- Handle switches ---------------------

LOCAL=false
STORAGES=false

if [[ "$1" == "-l" ]] || [[ "$1" == "--local" ]]; then
	LOCAL=true
elif [[ "$1" == "-s" ]] || [[ "$1" == "--storages" ]]; then
	STORAGES=true
fi

if [[ "$2" == "-l" ]] || [[ "$2" == "--local" ]]; then
	LOCAL=true
elif [[ "$2" == "-s" ]] || [[ "$2" == "--storages" ]]; then
	STORAGES=true
fi

# -------------- Check for required packages ---------------

# python3-venv

if /usr/bin/python3 -m venv 2>&1 | /bin/grep "is not available" > /dev/null; then
	/usr/bin/printf "${R}[-]${NC} Unresolved dependency: python3-venv. To install this package run:\n%s\n" \
                    "sudo apt install -y python3-venv"
	exit 1
fi

# p7zip-full

if ! /usr/bin/dpkg-query -W -f='${Status}' p7zip-full 2>&1 | /bin/grep "ok installed" > /dev/null; then
	/usr/bin/printf "${R}[-]${NC} Unresolved dependency: p7zip-full. To install this package run:\n%s\n" \
                    "sudo apt install -y p7zip-full"
	exit 1
fi

# ------------------- Create directories -------------------

# OPT

/usr/bin/printf "${W}[*]${NC} Creating directory: '${OPT}'\n"

if [[ -d "${OPT}" ]]; then
	/usr/bin/printf "${R}[-]${NC} ${OPT} already exists. First run:\n%s\n" \
                    "sudo uninstall.sh --all"
	exit 1
fi

if /bin/mkdir "${OPT}"; then
	/usr/bin/printf "${G}[+]${NC} Successfully created directory: '${OPT}'\n\n"
else
	/usr/bin/printf "${R}[-]${NC} Failed to create directory: '${OPT}'\n"
	exit 1
fi

# LOG

/usr/bin/printf "${W}[*]${NC} Creating directory: '${LOG}'\n"

if [[ -d "${LOG}" ]]; then
	/usr/bin/printf "${R}[-]${NC} ${LOG} already exists. First run:\n%s\n" \
                    "sudo uninstall.sh --all"
	exit 1
fi

if /bin/mkdir -p "${LOG}"; then
	/usr/bin/printf "${G}[+]${NC} Successfully created directory: '${LOG}'\n\n"
else
	/usr/bin/printf "${R}[-]${NC} Failed to create directory: '${LOG}'\n"
	exit 1
fi

# STORAGE

/usr/bin/printf "${W}[*]${NC} Creating directory: '${STORAGE}'\n"

if [[ -d "${STORAGE}" ]]; then
	/usr/bin/printf "${R}[-]${NC} ${STORAGE} already exists. First run:\n%s\n" \
                    "sudo uninstall.sh --all"
	exit 1
fi

if /bin/mkdir -p "${STORAGE}"; then
	/usr/bin/printf "${G}[+]${NC} Successfully created directory: '${STORAGE}'\n\n"
else
	/usr/bin/printf "${R}[-]${NC} Failed to create directory: '${STORAGE}'\n"
	exit 1
fi

# ------------ Build Python virtual environment ------------

/usr/bin/printf "${W}[*]${NC} Building Python virtual environment\n"

if /usr/bin/python3 -m venv "${OPT}/venv"; then
	/usr/bin/printf "${G}[+]${NC} Successfully builded Python virtual environment\n\n"
else
	/usr/bin/printf "${R}[-]${NC} Failed to build Python virtual environment\n"
	exit 1
fi

# ------------------------ Install -------------------------

/usr/bin/printf "${W}[*]${NC} Installing usbrip\n"

if $LOCAL; then
	if ${OPT}/venv/bin/python "${PWD}/setup.py" install; then
		/usr/bin/printf "${G}[+]${NC} Successfully installed usbrip using local dependencies\n\n"
	else
		/usr/bin/printf "${R}[-]${NC} Failed to install usbrip using local dependencies\n"
		exit 1
	fi
else
	if ${OPT}/venv/bin/pip install "${PWD}"; then
		/usr/bin/printf "${G}[+]${NC} Successfully installed usbrip using PyPI dependencies\n\n"
	else
		/usr/bin/printf "${R}[-]${NC} Failed to install usbrip using PyPI dependencies\n"
		exit 1
	fi
fi

${OPT}/venv/bin/python "${PWD}/setup.py" clean
/usr/bin/printf "\n"

# --------------------- Create symlink ---------------------

if [[ -e "${SYMLINK}" ]]; then
	/bin/rm "${SYMLINK}"
fi

if /bin/ln -s "${OPT}/venv/bin/usbrip" "${SYMLINK}"; then
	/usr/bin/printf "${G}[+]${NC} Created symlink: '${SYMLINK}'\n"
fi

# ----------------- Create usbrip storages -----------------

if $STORAGES; then
	# History

	/usr/bin/printf "${W}[*]${NC} Creating usbrip history storage\n"

	if createHistoryStorage; then
		/usr/bin/printf "${G}[+]${NC} Successfully created usbrip history storage\n\n"
	else
		/usr/bin/printf "${R}[-]${NC} Failed to create usbrip history storage\n"
		exit 1
	fi

	# Gen Auth

	/usr/bin/printf "${W}[*]${NC} Generating authorized device list\n"

	if generateAuthorizedDeviceList; then
		/usr/bin/printf "${G}[+]${NC} Successfully generated authorized device list\n\n"
	else
		/usr/bin/printf "${R}[-]${NC} Failed to generate authorized device list\n"
		exit 1
	fi

	# Violations

	/usr/bin/printf "${W}[*]${NC} Creating usbrip violations storage\n"

	if createViolationsStorage; then
		/usr/bin/printf "${G}[+]${NC} Successfully created usbrip violations storage\n\n"
	else
		/usr/bin/printf "${R}[-]${NC} Failed to create usbrip violations storage\n"
		exit 1
	fi
fi

# -------------------------- Done --------------------------

/usr/bin/printf "${G}[+]${NC} Done.\n"
