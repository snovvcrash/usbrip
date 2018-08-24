usbrip
==========
[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPLv3-blue.svg)](https://raw.githubusercontent.com/snovvcrash/usbrip/master/LICENSE)
[![Built with Love](https://img.shields.io/badge/built%20with-%F0%9F%92%97%F0%9F%92%97%F0%9F%92%97-lightgrey.svg)](https://emojipedia.org/growing-heart/)

[![Logo](https://user-images.githubusercontent.com/23141800/38119848-68883eea-33cd-11e8-98b5-4a33abbdd1dc.png)](#usbrip)

**usbrip** (derived from "USB Ripper", not "USB R.I.P." :hushed:) is an open source forensics tool with CLI interface that lets you keep track of USB device artifacts (a.k.a. *USB event history*: "Connected" and "Disconnected" events) on Linux machines.

Table of Contents:
  * [**Description**](#description)
  * [**Screenshots**](#screenshots)
  * [**Dependencies**](#dependencies)
    * [DEB Packages](#deb-packages)
    * [PIP Packages](#pip-packages)
  * [**Installation**](#installation)
  * [**Usage**](#usage)
    * [Synopsis](#synopsis)
    * [Help](#help)
  * [**Examples**](#examples)
  * [**Post Scriptum**](#post-scriptum)

Description
==========
usbrip is a small piece of software written in pure Python 3 (using some external modules though, see [Dependencies/PIP](#pip-packages)) which parses Linux log files (`/var/log/syslog*` or `/var/log/messages*` depending on the distro) for constructing USB event history tables. Such tables may contain the following columns: "Connected" (date & time), "User", "VID" (vendor ID), "PID" (product ID), "Product", "Manufacturer", "Serial Number", "Port" and "Disconnected" (date & time).

Besides, it also can:
* export gathered information as a JSON dump (and open such dumps, of course (: );
* generate a list of authorized (trusted) USB devices as a JSON (call it `auth.json`);
* search for "violation events" based on the `auth.json`: show (or generate another JSON with) USB devices that do appear in history and do NOT appear in the `auth.json`;
* *[when installed]* create crypted storages (7zip archives) to automatically backup and accumulate USB events with the help of `crontab` utility;
* search additional details about a specific USB device based on its VID and/or PID.

Screenshots
==========
![Screenshot-1](https://user-images.githubusercontent.com/23141800/40887882-e00d4d3a-6757-11e8-962c-c77331782b19.png "Get USB event history")
---
![Screenshot-2](https://user-images.githubusercontent.com/23141800/40886876-46c349d6-6748-11e8-92cf-0b0790ea9505.png "Search for extra details about a specific USB device")

Dependencies
==========
usbrip works with **non**-modified structure of system log files only, so, unfortunately, it won't be able to parse USB history if you change the format of syslogs (with `syslog-ng` or `rsyslog` for example). That's why the timestamps of "Connected" and "Disconnected" fields don't have the year, by the way. Keep that in mind.

## DEB Packages
  * python3.x (or newer) interpreter
  * python-virtualenv *(optional for portable mode)*
  * p7zip-full *(used by `storages` module)*

## PIP Packages
usbrip makes use of the following external modules:
  * [terminaltables](https://github.com/Robpol86/terminaltables "Robpol86/terminaltables: Generate simple tables in terminals from a nested list of strings.")
  * [termcolor](https://pypi.org/project/termcolor "termcolor · PyPI")

Resolve all Python dependencies with the `pip` one-liner:
```
$ python3 -m pip install -r requirements.txt
```

Installation
==========
usbrip can work in portable mode (when you run it explicity with `python3` command like in [Examples](#examples)) but it also can be installed on the system with the `install.sh` script.

When using the `install.sh` some extra features become available:
  * all the necessary [Python requirements](#python) are installed automatically (by creating virtual environment);
  * you can run usbrip from anywhere in your terminal with `usbrip` command;
  * you can set a crontab job to backup USB events on a schedule (the example of crontab jobs can be found in `usbrip.cron`).

:warning: **Warning**: if you are using the crontab scheduling, you want to configure the cron job with `sudo crontab -e` in order to force the `storage update` submodule run as root as well as protect the passwords of the USB event storages. It's obviously **not a truly secure way** to input passwords (no secrets should be ever stored as plain text / passed as arguments on the command line due to a variety of ways of exposing such secrets, e. g. scanning `/proc` directory for new PIDs to catch short-lived processes), but this is just an educational project in the end (interactive mode for secure password prompting is in TODO list :neutral_face:).

The `uninstall.sh` script removes all the installation artifacts from your system.

To install usbrip use:
```
$ git clone https://github.com/snovvcrash/usbrip.git usbrip && cd usbrip
$ chmod +x install.sh

# When -s switch is enabled, not only the usbrip project is installed, but also the list of trusted USB devices, history and violations storages are created
$ sudo -H ./install.sh [-s, --storages]
```
:warning: **Warning**: when using `-s` option during installation, make sure that system logs do contain at least one *external* USB device entry. It is a necessary condition for usbrip to successfully create the list of trusted devices (and as a result, successfully create the violations storage).

After the installation completes, feel free to remove the usbrip folder.

To uninstall usbrip use:
```
$ chmod +x uninstall.sh

# When -a switch is enabled, not only the usbrip project directory is deleted, but also all the storages and usbrip logs are deleted too
$ sudo ./uninstall.sh [-a, --all]
```

When installed, the usbrip uses the following paths:
  * `/opt/usbrip/` — project's main directory;
  * `/var/opt/usbrip/storage/` — USB event storages: `history.7z` and `violations.7z` (created during the installation process);
  * `/var/opt/usbrip/log/` — usbrip logs (recommended to log usbrip activity when using crontab, see `usbrip.cron`);
  * `/var/opt/usbrip/trusted/` — list of trusted USB devices (created during the installation process);
  * `/usr/local/bin/usbrip` — symlink to the `/opt/usbrip/usbrip.py` file.

Usage
==========
## Synopsis
```
# ---------- BANNER ----------

$ python3 usbrip.py banner
Get usbrip banner.

# ---------- EVENTS ----------

$ python3 usbrip.py events history [-t | -l] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--user <USER> [<USER> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-c <COLUMN> [<COLUMN> ...]] [-f <FILE> [<FILE> ...]] [-q] [--debug]
Get USB event history.

$ python3 usbrip.py events open <DUMP.JSON> [-t | -l] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--user <USER> [<USER> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-c <COLUMN> [<COLUMN> ...]] [-f <FILE> [<FILE> ...]] [-q] [--debug]
Open USB event dump.

$ python3 usbrip.py events gen_auth <OUT_AUTH.JSON> [-a <ATTRIBUTE> [<ATTRIBUTE> ...]] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--user <USER> [<USER> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-f <FILE> [<FILE> ...]] [-q] [--debug]
Generate a list of trusted (authorized) USB devices.

$ python3 usbrip.py events violations <IN_AUTH.JSON> [-a <ATTRIBUTE> [<ATTRIBUTE> ...]] [-t | -l] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--user <USER> [<USER> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-c <COLUMN> [<COLUMN> ...]] [-f <FILE> [<FILE> ...]] [-q] [--debug]
Get USB violation events based on the list of trusted devices.

# ---------- STORAGE ----------

$ python3 usbrip.py storage list <STORAGE_TYPE> -p <PASSWORD> [-q] [--debug]
List contents of the selected storage (7zip archive). STORAGE_TYPE is "history" or "violations".

$ python3 usbrip.py storage open <STORAGE_TYPE> -p <PASSWORD> [-t | -l] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--user <USER> [<USER> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-c <COLUMN> [<COLUMN> ...]] [-q] [--debug]
Open selected storage (7zip archive). Behaves similary to the EVENTS OPEN submodule.

$ python3 usbrip.py storage update <STORAGE_TYPE> -p <PASSWORD> [-a <ATTRIBUTE> [<ATTRIBUTE> ...]] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--user <USER> [<USER> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [--lvl <COMPRESSION_LEVEL>] [-q] [--debug]
Update storage — add USB events to the existing storage (7zip archive). COMPRESSION_LEVEL is a number in [0..9].

$ python3 usbrip.py storage create <STORAGE_TYPE> [-p <PASSWORD>] [-a <ATTRIBUTE> [<ATTRIBUTE> ...]] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--user <USER> [<USER> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [--lvl <COMPRESSION_LEVEL>] [-q] [--debug]
Create storage — create 7zip archive and add USB events to it according to the selected options.

$ python3 usbrip.py storage passwd <STORAGE_TYPE> -o <OLD_PASSWORD> -n <NEW_PASSWORD> [--lvl <COMPRESSION_LEVEL>] [-q] [--debug]
Change password of the existing storage.

# ---------- IDs ----------

$ python3 usbrip.py ids search [--vid <VID>] [--pid <PID>] [--offline] [-q] [--debug]
Get extra details about a specific USB device by its <VID> and/or <PID> from the USB ID database.

$ python3 usbrip.py ids download [-q] [--debug]
Update (download) the USB ID database.
```

## Help
To get a list of module names use:
```
$ python3 usbrip.py -h
```

To get a list of submodule names for a specific module use:
```
$ python3 usbrip.py <module> -h
```

To get a list of all switches for a specific submodule use:
```
$ python3 usbrip.py <module> <submodule> -h
```

Examples
==========
* Show the event history of all USB devices, supressing banner output, info messages and user iteraction (`-q`, `--quiet`), represented as a list (`-l`, `--list`) with latest 100 entries (`-n NUMBER`, `--number NUMBER`):
  ```
  $ python3 usbrip.py events history -ql -n 100
  ```

* Show the event history of the external USB devices (`-e`, `--external`, which were *actually* disconnected) represented as a table (`-t`, `--table`) containing "Connected", "VID", "PID", "Disconnected" and "Serial Number" columns (`-c COLUMN [COLUMN]`, `--column COLUMN [COLUMN]`) filtered by date (`-d DATE [DATE ...]`, `--date DATE [DATE ...]`) with logs taken from the outer files (`-f FILE [FILE ...]`, `--file FILE [FILE ...]`):
  ```
  $ python3 usbrip.py events history -et -c conn vid pid disconn serial -d "Dec  9" "Dec 10" -f /var/log/syslog.1 /var/log/syslog.2.gz
  ```

* Build the event history of all USB devices and redirect the output to a file for further analysis. When the output stream is NOT terminal stdout (`|` or `>` for example) there would be no ANSI escape characters (color) in the output so feel free to use it that way. Also notice that usbrip uses some UNICODE symbols so it would be nice to convert the resulting file to UTF-8 encoding (with `encov` for example) as well as change newline characters to Windows style for portability (with `awk` for example):
  ```
  python3 usbrip.py history events -t | awk '{ sub("$", "\r"); print }' > usbrip.txt && enconv -x UTF8 usbrip.txt
  ```

  *Remark*: you can always get rid of the escape characters by yourself even if you have already got the output to stdout. To do that just copy the output data to `usbrip.txt` and add one more `awk` instruction:

  ```
  awk '{ sub("$", "\r"); gsub("\\x1B\\[[0-?]*[ -/]*[@-~]", ""); print }' usbrip.txt && enconv -x UTF8 usbrip.txt
  ```

* Generate a list of trusted USB devices as a JSON-file (`trusted/auth.json`) with "VID" and "PID" attributes containing the first *three* devices connected on September 26:
  ```
  $ python3 usbrip.py events gen_auth trusted/auth.json -a vid pid -n 3 -d "Sep 26"
  ```

* Search the event history of the external USB devices for violations based on the list of trusted USB devices (`trusted/auth.json`) by "PID" attribute, restrict resulting events to those which have "Bob" as a user, "EvilUSBManufacturer" as a manufacturer, "1234567890" as a serial number and represent the output as a table with "Connected", "VID" and "PID" columns:
  ```
  $ python3 usbrip.py events violations trusted/auth.json -a pid -et --user Bob --manufact EvilUSBManufacturer --serial 1234567890 -c conn vid pid
  ```

* Search for details about a specific USB device by its VID (`--vid VID`) and PID (`--pid PID`):
  ```
  $ python3 usbrip.py ids search --vid 0781 --pid 5580
  ```

* Download the latest version of `usb_ids/usb.ids` database (the source is [here](http://www.linux-usb.org/usb.ids "List of USB ID's")):
  ```
  $ python3 usbrip.py ids download
  ```

Post Scriptum
==========
Yep, the banner and info messages style is inspired by the *sqlmap* project :see_no_evil:

If this tool has been useful for you, feel free to buy me a coffee :coffee:

[![Coffee](https://user-images.githubusercontent.com/23141800/44239262-2cf7d680-a1c1-11e8-96b4-c4949f84e94e.png)](https://buymeacoff.ee/snovvcrash)
