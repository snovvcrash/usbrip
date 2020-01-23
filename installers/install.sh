#!/usr/bin/env bash

: '
%file install.sh
%author Sam Freeside (@snovvcrash) <snovvcrash@protonmail[.]ch>
%date 2018-05-28

%brief usbrip installer.

%license
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
%endlicense
'

# Usage: sudo -H bash installers/install.sh [-l/--local] [-s/--storages]

shopt -s expand_aliases

# ----------------------- Constants ------------------------

USER_HOME=`getent passwd ${SUDO_USER} | cut -d: -f6`
CONFIG="${USER_HOME}/.config/usbrip"

OPT="/opt/usbrip"
VAR_OPT="/var/opt/usbrip"
SYMLINK="/usr/local/bin/usbrip"

G="\033[1;32m"  # GREEN
Y="\033[1;33m"  # YELLOW
R="\033[1;31m"  # RED
W="\033[1;37m"  # WHITE
NC="\033[0m"    # NO COLOR

# ----------------------- Functions ------------------------

create_directory() {
	/usr/bin/printf "${W}>>>>${NC} Creating directory: '$1'\n"

	if [[ -d "$1" ]]; then
		/usr/bin/printf "${R}>>>>${NC} $1 already exists. First run:\n%s\n" \
						"sudo uninstall.sh --all"
		exit 1
	fi

	if /bin/mkdir -p "$1"; then
		/usr/bin/printf "${G}>>>>${NC} Successfully created directory: '$1'\n\n"
	else
		/usr/bin/printf "${R}>>>>${NC} Failed to create directory: '$1'\n"
		exit 1
	fi
}

# --------------------- usbrip aliases ---------------------

alias createHistoryStorage="${OPT}/venv/bin/usbrip storage create history -e"

alias generateAuthorizedDeviceList="${OPT}/venv/bin/usbrip events gen_auth -e -a vid pid"

alias createViolationsStorage="${OPT}/venv/bin/usbrip storage create violations -e -a vid pid"

# --------------- Check for root privileges ----------------

if [[ $EUID -ne 0 ]]; then
	/usr/bin/printf "${R}>>>>${NC} Please run as root:\nsudo %s\n" "${0}"
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

if ! /usr/bin/dpkg-query -W -f='${Status}' python3-venv 2>&1 | /bin/grep "ok installed" > /dev/null; then
	/usr/bin/printf "${Y}>>>>${NC} Unresolved dependency: python3-venv. Do you want to install this package as:\n%s\n" \
                    "\"sudo apt install python3-venv -y\"?"
	select YN in "Yes" "No"; do
		case ${YN} in
			"Yes" )
				$(which apt) install "python3-venv" -y
				break
				;;
			"No" )
				exit 1
				;;
		esac
	done
fi

# p7zip-full

if ! /usr/bin/dpkg-query -W -f='${Status}' p7zip-full 2>&1 | /bin/grep "ok installed" > /dev/null && ${STORAGES}; then
	/usr/bin/printf "${Y}>>>>${NC} Unresolved dependency: p7zip-full. Do you want to install this package as:\n%s\n" \
                    "\"sudo apt install p7zip-full -y\"?"
	select YN in "Yes" "No"; do
		case ${YN} in
			"Yes" )
				$(which apt) install "p7zip-full" -y
				break
				;;
			"No" )
				exit 1
				;;
		esac
	done
fi

# ------------------- Create directories -------------------

# OPT

create_directory "${OPT}"

# LOG

create_directory "${VAR_OPT}/log"

# STORAGE

create_directory "${VAR_OPT}/storage"

# CONFIG

create_directory "${CONFIG}"

# -------------------- Fix permissions ---------------------

chmod -R 600 "${VAR_OPT}/log"

# ------------ Build Python virtual environment ------------

/usr/bin/printf "${W}>>>>${NC} Building Python virtual environment\n"

if /usr/bin/python3 -m venv "${OPT}/venv"; then
	/usr/bin/printf "${G}>>>>${NC} Successfully builded Python virtual environment\n\n"
else
	/usr/bin/printf "${R}>>>>${NC} Failed to build Python virtual environment\n"
	exit 1
fi

# ------------------------ Install -------------------------

/usr/bin/printf "${W}>>>>${NC} Installing usbrip\n"

if $LOCAL; then
	if ${OPT}/venv/bin/python "${PWD}/setup.py" install; then
		/usr/bin/printf "${G}>>>>${NC} Successfully installed usbrip using local dependencies\n\n"
	else
		/usr/bin/printf "${R}>>>>${NC} Failed to install usbrip using local dependencies\n"
		exit 1
	fi
else
	if ${OPT}/venv/bin/pip install "${PWD}"; then
		/usr/bin/printf "${G}>>>>${NC} Successfully installed usbrip using PyPI dependencies\n\n"
	else
		/usr/bin/printf "${R}>>>>${NC} Failed to install usbrip using PyPI dependencies\n"
		exit 1
	fi
fi

${OPT}/venv/bin/python "${PWD}/setup.py" clean
echo

# ----------------------- Copy files -----------------------

if /usr/bin/cp "${PWD}/usbrip/usb_ids/usb.ids" "${USER_HOME}/.config/usbrip/usb.ids"; then
	/usr/bin/printf "${G}>>>>${NC} Successfully copied usb.ids database\n\n"
else
	/usr/bin/printf "${R}>>>>${NC} Failed copy usb.ids database\n"
	exit 1
fi

if /usr/bin/cp "${PWD}/usbrip/cron/usbrip.cron" "${USER_HOME}/.config/usbrip/usbrip.cron"; then
	/usr/bin/printf "${G}>>>>${NC} Successfully copied usbrip cron job example\n\n"
else
	/usr/bin/printf "${R}>>>>${NC} Failed copy usbrip cron job example\n"
	exit 1
fi

chown -R ${SUDO_USER} ${USER_HOME}/.config

# --------------------- Create symlink ---------------------

if [[ -e "${SYMLINK}" ]]; then
	/bin/rm "${SYMLINK}"
fi

if /bin/ln -s "${OPT}/venv/bin/usbrip" "${SYMLINK}"; then
	/usr/bin/printf "${G}>>>>${NC} Created symlink: '${SYMLINK}'\n"
fi

# ----------------- Create usbrip storages -----------------

if ${STORAGES}; then
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
