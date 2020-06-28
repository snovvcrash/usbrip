<p align="center">
  <a href="#"><img src="https://user-images.githubusercontent.com/23141800/56420194-b9551e80-62a5-11e9-8508-fc0f4a398042.png" alt="logo.png" /></a>
</p>

----------

<p align="center">
  <a href="https://github.com/snovvcrash/usbrip/blob/master/usbrip/__init__.py#L24"><img src="https://img.shields.io/badge/GitHub%20ver-2.2.2%E2%80%900-success.svg?logo=github&logoColor=white" alt="github-version.svg" /></a>
  <a href="https://pypi.org/project/usbrip/#history"><img src="https://img.shields.io/badge/PyPI%20ver-2.2.2%E2%80%900-3775a9.svg?logo=pypi&logoColor=white" alt="pypi-version.svg" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.6-3776ab.svg?logo=python&logoColor=white" alt="python-version.svg" /></a>
  <a href="https://raw.githubusercontent.com/snovvcrash/usbrip/master/LICENSE"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="license.svg" /></a>
  <a href="https://repology.org/project/usbrip/versions"><img src="https://repology.org/badge/version-for-repo/blackarch/usbrip.svg?header=BlackArch pkg" alt="blackarch-package.svg"></a>
  <a href="https://emojipedia.org/growing-heart/"><img src="https://img.shields.io/badge/built%20with-%F0%9F%92%97%F0%9F%92%97%F0%9F%92%97-lightgrey.svg" alt="built-with-love.svg" /></a>
</p>

**usbrip** (inherited from "USB Ripper", not "USB R.I.P.") is a simple forensics tool with command line interface that lets you keep track of USB device artifacts (i.e., USB event history) on Linux machines.

Table of Contents:

* [**Description**](#description)
* [**Quick Start**](#quick-start)
* [**Showcase**](#showcase)
* [**Dependencies**](#dependencies)
  - [System Log Structure](#system-log-structure)
  - [DEB Packages](#deb-packages)
  - [pip Packages](#pip-packages)
* [**Manual installation**](#manual-installation)
  - [Git Clone](#git-clone)
  - [`install.sh`](#installsh)
    * [Paths](#paths)
    * [cron](#cron)
    * [`uninstall.sh`](#uninstallsh)
* [**Usage**](#usage)
  - [Synopsis](#synopsis)
  - [Help](#help)
* [**Examples**](#examples)
* [**TODO**](#todo)
* [**Credits & References**](#credits--references)
* [**Post Scriptum**](#post-scriptum)

Description
==========

**usbrip** is a small piece of software which analyzes Linux log data: `journalctl` output or contents of `/var/log/syslog*` (`/var/log/messages*`) files. Based on the collected data usbrip can build USB event history tables with the following columns:

* "Connected" (date & time);
* "Host";
* "VID" (vendor ID);
* "PID" (product ID);
* "Product";
* "Manufacturer";
* "Serial Number";
* "Port";
* "Disconnected" (date & time).

Besides, it also can:

* export collected data as a JSON dump for later use;
* generate a list of authorized *(trusted)* USB devices as a JSON file (call it `auth.json`);
* search for "violation events" based on the `auth.json`: discover USB devices that do appear in history **and** do NOT appear in the `auth.json`;
* *\*when installed with `-s` flag\** create protected storages (7-Zip archives) to automatically backup and accumulate USB events with the help of `crontab` scheduler;
* search additional details about a specific USB device based on its VID and/or PID.

Quick Start
==========

**Way 1.** Install the PyPI version with pip:

```
~$ curl https://bootstrap.pypa.io/get-pip.py | python3
~$ python3 -m pip install --upgrade usbrip
~$ usbrip --help
```

**Way 2.** Install the bleeding-edge version with [`install.sh`](#manual-installation):

```
~$ sudo apt install python3-venv p7zip-full -y
~$ git clone https://github.com/snovvcrash/usbrip.git usbrip && cd usbrip
~/usbrip$ sudo -H installers/install.sh
~/usbrip$ cd
~$ usbrip --help
```

Showcase
==========

![screenshot.png](https://user-images.githubusercontent.com/23141800/85950258-7c35f300-b964-11ea-8243-1928f48e877a.png)

[**Docker**](https://hub.docker.com/r/snovvcrash/usbrip) (\*DEMO ONLY!\*)

```
~$ docker run --rm -it snovvcrash/usbrip
```

Dependencies
==========

## System Log Structure

usbrip supports two types of timestamps within system log files:

1. **Non-modified** — standard `syslog` structure for GNU/Linux ([`"%b %d %H:%M:%S"`](http://strftime.org/), ex. `"Jan  1 00:00:00"`). This type of timestamp does not provide the information about years.
2. **Modified** (recommended) — better `syslog` structure which provides high precision timestamps including years ([`"%Y-%m-%dT%H:%M:%S.%f%z"`](http://strftime.org/), ex. `"1970-01-01T00:00:00.000000-00:00"`).

If you do have `journalctl` installed, then there's nothing to worry about as it can convert timestamps on the fly.

Otherwise, the desired `syslog` structure could be achieved by setting `RSYSLOG_FileFormat` format in rsyslog configuration.

1. Comment out the following line in `/etc/rsyslog.conf`:

```
$ActionFileDefaultTemplate RSYSLOG_TraditionalFileFormat
```

2. Add custom *.conf* file for usbrip:

```
~$ echo '$ActionFileDefaultTemplate RSYSLOG_FileFormat' | sudo tee /etc/rsyslog.d/usbrip.conf
```

3. *(optional)* Delete existing log files:

```
~$ sudo rm -f /var/log/syslog* /var/log/messages*
```

4. Restart the service:

```
~$ sudo systemctl restart rsyslog
```

Firstly, usbrip will check if there is a chance to dump system events using `journalctl` as the most portable option. If not — it will search for and parse `/var/log/syslog*` and `/var/log/messages*` system log files.

## DEB Packages

* python3.6 (or newer) interpreter;
* python3-venv;
* p7zip-full (used by `storages` module).

## pip Packages

* [terminaltables](https://github.com/Robpol86/terminaltables "Robpol86/terminaltables: Generate simple tables in terminals from a nested list of strings.")
* [termcolor](https://pypi.org/project/termcolor "termcolor · PyPI")
* [tqdm](https://github.com/tqdm/tqdm "tqdm/tqdm: A Fast, Extensible Progress Bar for Python and CLI")

Manual installation
==========

## Git Clone

For simplicity, lets agree that all the commands where `~/usbrip$` prefix is appeared are executed in the `~/usbrip` directory which is created as a result of git clone:

```
~$ git clone https://github.com/snovvcrash/usbrip.git usbrip && cd usbrip
```

## `install.sh`

Besides installing with pip, usbrip can also be installed with custom `installers/install.sh` script.

When using `install.sh` some extra features become available:

* the virtual environment is created automatically;
* the `storage` module becomes available: you can set a crontab job to backup USB events on a schedule (the example of crontab jobs can be found in `usbrip/cron/usbrip.cron`).

:warning: **Warning:** if you are using the crontab scheduling, you want to configure the cron job with `sudo crontab -e` in order to force the `storage update` submodule run as root. The storage passwords are kept in `/var/opt/usbrip/usbrip.ini` and accessible by root only by default.

To install usbrip use:

```
~/usbrip$ sudo -H installers/install.sh [-l/--local] [-s/--storages]
~/usbrip$ cd
~$ usbrip --help
```

* When `-l` switch is enabled, Python dependencies are resolved from local `.tar` packages (`./3rdPartyTools/`) instead of PyPI.
* When `-s` switch is enabled, not only the usbrip project is installed, but also the list of trusted USB devices, history and violations storages are created.

After the installation completes, feel free to remove the `~/usbrip` directory.

### Paths

When installed with `install.sh`, the usbrip uses the following paths:

* `/opt/usbrip/` — project's main directory;
* `/var/opt/usbrip/usbrip.ini` — usbrip configuration file (keeps passwords for 7-Zip storages);
* `/var/opt/usbrip/storage/` — USB event storages: `history.7z` and `violations.7z` (created during the installation process);
* `/var/opt/usbrip/log/` — usbrip logs (recommended to log usbrip activity when using crontab, see `usbrip/cron/usbrip.cron`);
* `/var/opt/usbrip/trusted/` — list of trusted USB devices (created during the installation process);
* `/usr/local/bin/usbrip` — symlink to the `/opt/usbrip/venv/bin/usbrip` script.

### cron

Cron jobs can be set as follows:

```
~/usbrip$ sudo crontab -l > tmpcron && echo "" >> tmpcron
~/usbrip$ cat usbrip/cron/usbrip.cron | tee -a tmpcron
~/usbrip$ sudo crontab tmpcron
~/usbrip$ rm tmpcron
```

### `uninstall.sh`

The `installers/uninstall.sh` script removes usbrip and all the installation artifacts from your system.

To uninstall usbrip use:

```
~/usbrip$ sudo installers/uninstall.sh [-a/--all]
```

* When `-a` switch is enabled, not only the usbrip project directory is deleted, but also all the storages and usbrip logs are deleted too.

Don't forget to remove the cron job if you had set up one.

Usage
==========

## Synopsis

```
# ---------- BANNER ----------

$ usbrip banner
Get usbrip banner.

# ---------- EVENTS ----------

$ sudo usbrip events history [-t | -l] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--host <HOST> [<HOST> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-c <COLUMN> [<COLUMN> ...]] [-f <FILE> [<FILE> ...]] [-q] [--debug]
Get USB event history.

$ sudo usbrip events open <DUMP.JSON> [-t | -l] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--host <HOST> [<HOST> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-c <COLUMN> [<COLUMN> ...]] [-f <FILE> [<FILE> ...]] [-q] [--debug]
Open USB event dump.

$ sudo usbrip events genauth <OUT_AUTH.JSON> [-a <ATTRIBUTE> [<ATTRIBUTE> ...]] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--host <HOST> [<HOST> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-f <FILE> [<FILE> ...]] [-q] [--debug]
Generate a list of trusted (authorized) USB devices.

$ sudo usbrip events violations <IN_AUTH.JSON> [-a <ATTRIBUTE> [<ATTRIBUTE> ...]] [-t | -l] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--host <HOST> [<HOST> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-c <COLUMN> [<COLUMN> ...]] [-f <FILE> [<FILE> ...]] [-q] [--debug]
Get USB violation events based on the list of trusted devices.

# ---------- STORAGE ----------

$ sudo usbrip storage list <STORAGE_TYPE> [-q] [--debug]
List contents of the selected storage. STORAGE_TYPE is "history" or "violations".

$ sudo usbrip storage open <STORAGE_TYPE> [-t | -l] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--host <HOST> [<HOST> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [-c <COLUMN> [<COLUMN> ...]] [-q] [--debug]
Open selected storage. Behaves similarly to the EVENTS OPEN submodule.

$ sudo usbrip storage update <STORAGE_TYPE> [IN_AUTH.JSON] [-a <ATTRIBUTE> [<ATTRIBUTE> ...]] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--host <HOST> [<HOST> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [--lvl <COMPRESSION_LEVEL>] [-q] [--debug]
Update storage -- add USB events to the existing storage. COMPRESSION_LEVEL is a number in [0..9].

$ sudo usbrip storage create <STORAGE_TYPE> [IN_AUTH.JSON] [-a <ATTRIBUTE> [<ATTRIBUTE> ...]] [-e] [-n <NUMBER_OF_EVENTS>] [-d <DATE> [<DATE> ...]] [--host <HOST> [<HOST> ...]] [--vid <VID> [<VID> ...]] [--pid <PID> [<PID> ...]] [--prod <PROD> [<PROD> ...]] [--manufact <MANUFACT> [<MANUFACT> ...]] [--serial <SERIAL> [<SERIAL> ...]] [--port <PORT> [<PORT> ...]] [--lvl <COMPRESSION_LEVEL>] [-q] [--debug]
Create storage -- create 7-Zip archive and add USB events to it according to the selected options.

$ sudo usbrip storage passwd <STORAGE_TYPE> [--lvl <COMPRESSION_LEVEL>] [-q] [--debug]
Change password of the existing storage.

# ---------- IDs ----------

$ usbrip ids search [--vid <VID>] [--pid <PID>] [--offline] [-q] [--debug]
Get extra details about a specific USB device by its <VID> and/or <PID> from the USB ID database.

$ usbrip ids download [-q] [--debug]
Update (download) the USB ID database.
```

## Help

To get a list of module names use:

```
~$ usbrip --help
```

To get a list of submodule names for a specific module use:

```
~$ usbrip <module> --help
```

To get a list of all switches for a specific submodule use:

```
~$ usbrip <module> <submodule> --help
```

Examples
==========

* Show the event history of all USB devices, suppressing banner output, info messages and user interaction (`-q`, `--quiet`), represented as a list (`-l`, `--list`) with latest 100 entries (`-n NUMBER`, `--number NUMBER`):

  ```
  ~$ sudo usbrip events history -ql -n 100
  ```

* Show the event history of the external USB devices (`-e`, `--external`, which were *actually* disconnected) represented as a table (`-t`, `--table`) containing "Connected", "VID", "PID", "Disconnected" and "Serial Number" columns (`-c COLUMN [COLUMN ...]`, `--column COLUMN [COLUMN ...]`) filtered by date (`-d DATE [DATE ...]`, `--date DATE [DATE ...]`) and PID (`--pid <PID> [<PID> ...]`) with logs taken from the outer files (`-f FILE [FILE ...]`, `--file FILE [FILE ...]`):

  ```
  ~$ sudo usbrip events history -et -c conn vid pid disconn serial -d '1995-09-15' '2018-07-01' --pid 1337 -f /var/log/syslog.1 /var/log/syslog.2.gz
  ```

  :alien: **Note:** there is a thing to remember when working with filters. There are 4 types of filtering available: only *external* USB events (devices that can be pulled out easily, `-e`); *by date* (`-d`); *by fields* (`--host`, `--vid`, `--pid`, `--product`, `--manufact`, `--serial`, `--port`) and *by number of entries* you get as the output (`-n`). When applying different filters simultaneously, you will get the following behavior: firstly, *external* and *by date* filters are applied, then usbrip will search for specified *field* values in the intersection of the last two filters, and in the end it will cut the output to the *number* you defined with the `-n` option. So think of it as an **intersection** for *external* and *by date* filtering and **union** for *by fields* filtering. Hope it makes sense.

* Build the event history of all USB devices and redirect the output to a file for further analysis. When the output stream is NOT terminal stdout (`|` or `>` for example) there would be no ANSI escape characters (color) in the output so feel free to use it that way. Also notice that usbrip uses some UNICODE symbols so it would be nice to convert the resulting file to UTF-8 encoding (with `encov` for example) as well as change newline characters to Windows style for portability (with `awk` for example):

  ```
  ~$ sudo usbrip history events -t | awk '{ sub("$", "\r"); print }' > usbrip.out && enconv -x UTF8 usbrip.out
  ```

  *Remark*: you can always get rid of the escape characters by yourself even if you have already got the output to stdout. To do that just copy the output data to `usbrip.out` and add one more `awk` instruction:

  ```
  ~$ awk '{ sub("$", "\r"); gsub("\\x1B\\[[0-?]*[ -/]*[@-~]", ""); print }' usbrip.out && enconv -x UTF8 usbrip.out
  ```

* Generate a list of trusted USB devices as a JSON-file (`trusted/auth.json`) with "VID" and "PID" attributes containing the first *three* devices connected on November 30, 1984:

  ```
  ~$ sudo usbrip events genauth trusted/auth.json -a vid pid -n 3 -d '1984-11-30'
  ```

  :warning: **Warning:** there are cases when different USB flash drives might have identical serial numbers. This could happen as a result of a [manufacturing error](https://forums.anandtech.com/threads/changing-creating-a-custom-serial-id-on-a-flash-drive-low-level-blocks.2099116/) or just some black hats were able to rewrite the drive's memory chip which turned out to be non-one-time programmable and so on... Anyways, *"No system is safe"*. usbrip **does not** handle such cases in a smart way so far, namely it will treat a pair of devices with identical SNs (if there exists one) as the same device regarding to the trusted device list and `genauth` module.

* Search the event history of the external USB devices for violations based on the list of trusted USB devices (`trusted/auth.json`) by "PID" attribute, restrict resulting events to those which have "Bob-PC" as a hostname, "EvilUSBManufacturer" as a manufacturer, "0123456789" as a serial number and represent the output as a table with "Connected", "VID" and "PID" columns:

  ```
  ~$ sudo usbrip events violations trusted/auth.json -a pid -et --host Bob-PC --manufact EvilUSBManufacturer --serial 0123456789 -c conn vid pid
  ```

* Search for details about a specific USB device by its VID (`--vid VID`) and PID (`--pid PID`):

  ```
  ~$ usbrip ids search --vid 0781 --pid 5580
  ```

* Download the latest version of `usb.ids` [database](http://www.linux-usb.org/usb.ids "List of USB ID's"):

  ```
  ~$ usbrip ids download
  ```

TODO
==========

* [ ] Migrate from 7-Zip archives as the protected storages to SQLite DB

Credits & References
==========

* [usbrip / Инструменты Kali Linux](https://kali.tools/?p=4873)
* [Как узнать, какие USB устройства подключались к Linux / HackWare.ru](https://hackware.ru/?p=9703)
* [Linux-форензика в лице трекинга истории подключений USB-устройств / Хабр](https://habr.com/ru/post/352254/)
* [Linux Forensics! First Look at usbrip / YouTube / 13Cubed](https://youtu.be/DP4ScSp_2yE)

Post Scriptum
==========

If this tool has been useful for you, feel free to buy me a coffee.

[![coffee.png](https://user-images.githubusercontent.com/23141800/44239262-2cf7d680-a1c1-11e8-96b4-c4949f84e94e.png)](https://buymeacoff.ee/snovvcrash)
