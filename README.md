usbrip
========
[![Python Version](https://img.shields.io/badge/python-3.4,%203.5,%203.6-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPLv3-red.svg)](https://raw.githubusercontent.com/snovvcrash/usbrip/master/LICENSE)

usbrip (derived from "USB Ripper", not "USB R.I.P." :hushed:) is an open source forensics tool with CLI interface that lets you keep track of USB device artifacts (a.k.a. *USB event history*: "Connected" and "Disconnected" events) on Linux machines.

Table of contents:
  * [**Description**](#description)  
  * [**Screenshots**](#screenshots)  
  * [**Usage**](#usage)  
  * [**Examples**](#examples)  
  * [**Dependencies**](#dependencies)  
  * [**Post Scriptum**](#post-scriptum)

Description
========
usbrip is a small piece of software written in pure Python 3 (using some external modules though, see [Dependencies](#dependencies)) which parses Linux log files (`/var/log/syslog*` or `/var/log/messages*` depending on the distro) for constructing USB event history tables. Such tables may contain the following columns: "Connected" (date & time), "User", "VID" (vendor ID), "PID" (product ID), "Product", "Manufacturer", "Serial Number", "Port" and "Disconnected" (date & time).

Besides, it also can:
* generate a list of authorized (trusted) USB devices as a JSON (call it `auth.json`);
* search for "violation events" based on `auth.json`: show (or generate another JSON with) all USB devices that do appear in history but do NOT appear in `auth.json`;
* search additional details about a specific USB device base on its VID and/or PID.

Screenshots
========
![Screenshot-1](https://user-images.githubusercontent.com/23141800/37735126-2b601742-2d5e-11e8-85ed-9945123f484e.png "Get USB event history of external devices")
![Screenshot-2](https://user-images.githubusercontent.com/23141800/37735847-4340b720-2d60-11e8-83ce-b77c2b0673f8.png "Search for USB devices by PID")

Usage
========
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
========
* Show event history of all USB devices without asking about the generation method of the output (`-q`, `--quite`, default output to the terminal stdout) represented as list (`-l`, `--list`) with latest 100 entries (`-n NUMBER`, `--number NUMBER`):
  ```
  $ python3 usbrip.py events history -ql -c conn vid pid disconn serial -n 100
  ```

* Show event history of external USB devices (`-e`, `--external`, which were *actually* disconnected) with asking about the generation method of the output (default or as a JSON-file) represented as table (`-t`, `--table`) sorted by date (`-d DATES`, `--dates DATES`) with logs taken from the outer files (`-f FILES`, `--files FILES`):
  ```
  $ python3 usbrip.py events history -et -c conn vid pid disconn serial -d "Mar  3" "Mar 21" -f /var/log/syslog.1 /var/log/syslog.2.gz
  ```

* Build event history of all USB events and redirect the output to file for further analysis. When the output stream is NOT terminal stdout (`|` or `>` for example) there would be no ANSI escape characters (color) in the output so feel free to use it that way. Also notice that usbrip uses some UNICODE symbols so it would be nice to convert the resulting file to UTF-8 encoding (with `encov` for example) as well as replace newline characters to Windows style for portability (with `awk` for example):
  ```
  python3 usbrip.py history events -t | awk '{ sub("$", "\r"); print }' > usbrip.txt && enconv -x UTF8 usbrip.txt
  ```

  *Remark*: you can always get rid of the escape characters by yourself even if you have already got the output to stdout. To do that just copy the output data to `usbrip.txt` and write one more awk instruction:

  ```
  awk '{ sub("$", "\r"); gsub("\\x1B\\[[0-?]*[ -/]*[@-~]", ""); print }' usbrip.txt && enconv -x UTF8 usbrip.txt
  ```

* Generate a list of trusted USB devices as a JSON-file (`-o OUTPUT`, `--output OUTPUT`):
  ```
  $ python3 usbrip.py events gen_auth -o trusted/auth.json
  ```

* Search for violation events with asking about the generation method of the output (default or as a JSON-file):
  ```
  $ python3 usbrip.py events violations -i trusted/auth.json
  ```

* Search for details about a specific USB device by its VID and PID:
  ```
  $ python3 usbrip.py ids search --vid 0781 --pid 5580
  ```

* Download the latest version of `usb_ids/usb.ids` database from [here](http://www.linux-usb.org/usb.ids "List of USB ID's"):
  ```
  $ python3 usbrip.py ids download
  ```
  
Dependencies
========
usbrips makes use of the following external modules:
* [terminaltables](https://robpol86.github.io/terminaltables/v3.1.0/index.html "terminaltables 3.1.0 — terminaltables")
* [termcolor](https://pypi.python.org/pypi/termcolor "termcolor 1.1.0 : Python Package Index")
* [bs4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/ "Beautiful Soup Documentation — Beautiful Soup 4.4.0 documentation")

All requirements are stated in `requirements.txt`.

Post Scriptum
========
Yep, the logo and info messages style is inspired by the *sqlmap* project :see_no_evil:
