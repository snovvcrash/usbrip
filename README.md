usbrip
==========
[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPLv3-red.svg)](https://raw.githubusercontent.com/snovvcrash/usbrip/master/LICENSE)

![Logo](https://user-images.githubusercontent.com/23141800/38119848-68883eea-33cd-11e8-98b5-4a33abbdd1dc.png "usbrip")

usbrip (derived from "USB Ripper", not "USB R.I.P." :hushed:) is an open source forensics tool with CLI interface that lets you keep track of USB device artifacts (a.k.a. *USB event history*: "Connected" and "Disconnected" events) on Linux machines.

Table of Contents:
  * [**Description**](#description)  
  * [**Screenshots**](#screenshots)  
  * [**Usage**](#usage)  
  * [**Examples**](#examples)  
  * [**Dependencies**](#dependencies)  
  * [**Post Scriptum**](#post-scriptum)

Description
==========
usbrip is a small piece of software written in pure Python 3 (using some external modules though, see [Dependencies](#dependencies)) which parses Linux log files (`/var/log/syslog*` or `/var/log/messages*` depending on the distro) for constructing USB event history tables. Such tables may contain the following columns: "Connected" (date & time), "User", "VID" (vendor ID), "PID" (product ID), "Product", "Manufacturer", "Serial Number", "Port" and "Disconnected" (date & time).

Besides, it also can:
* generate a list of authorized (trusted) USB devices as a JSON (call it `auth.json`);
* search for "violation events" based on `auth.json`: show (or generate another JSON with) USB devices that do appear in history and do NOT appear in `auth.json`;
* search additional details about a specific USB device based on its VID and/or PID.

Screenshots
==========
![Screenshot-1](https://user-images.githubusercontent.com/23141800/37994964-c6eacb82-321b-11e8-9592-7ed6b291245c.png "Get USB event history of external devices")
![Screenshot-2](https://user-images.githubusercontent.com/23141800/37994970-c9db71e8-321b-11e8-87b0-db90c2d55f3c.png "Search for USB devices by PID")

Usage
==========
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
* Show the event history of all USB devices, supressing banner output, info messages and user iteraction (`-q`, `--quite`), represented as a list (`-l`, `--list`) with latest 100 entries (`-n NUMBER`, `--number NUMBER`):
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

* Generate a list of trusted USB devices as a JSON-file (`trusted/auth.json`) containing the first *three* devices connected on September 26:
  ```
  $ python3 usbrip.py events gen_auth trusted/auth.json -n 3 -d "Sep 26"
  ```

* Search the event history of the external USB devices for violations based on the list of trusted USB devices (`trusted/auth.json`) and represent the output as a table with "Connected", "VID" and "PID" columns:
  ```
  $ python3 usbrip.py events violations trusted/auth.json -et -c conn vid pid
  ```

* Search for details about a specific USB device by its VID (`--vid VID`) and PID (`--pid PID`):
  ```
  $ python3 usbrip.py ids search --vid 0781 --pid 5580
  ```

* Download the latest version of `usb_ids/usb.ids` database (the source is [here](http://www.linux-usb.org/usb.ids "List of USB ID's")):
  ```
  $ python3 usbrip.py ids download
  ```
  
Dependencies
==========
usbrip makes use of the following external modules:
* [terminaltables](https://robpol86.github.io/terminaltables/v3.1.0/index.html "terminaltables 3.1.0 — terminaltables")
* [termcolor](https://pypi.python.org/pypi/termcolor "termcolor 1.1.0 : Python Package Index")
* [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/ "Beautiful Soup Documentation — Beautiful Soup 4.4.0 documentation")

All requirements are stated in `requirements.txt`.

Post Scriptum
==========
Yep, the logo and info messages style is inspired by the *sqlmap* project :see_no_evil:
