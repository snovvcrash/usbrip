#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import string
from glob import glob
from datetime import datetime
from random import random, randint, choices

CHARSET = string.digits + 'ABCDEF'


def strftime_prop(start, end, prop, fmt):
	stime = time.mktime(time.strptime(start, fmt))
	etime = time.mktime(time.strptime(end, fmt))
	ptime = stime + prop * (etime - stime)
	return time.strftime(fmt, time.localtime(ptime))


def random_date(start, end, prop, fmt='%Y %b %d %H:%M:%S'):
	return strftime_prop(start, end, prop, fmt)


def date_offset(date, fmt='%Y %b %d %H:%M:%S'):
	return time.strftime(fmt, time.localtime(time.mktime(time.strptime(date, fmt)) + randint(1, 60)))


if __name__ == '__main__':
	for f in glob('/var/log/syslog*'):
		os.remove(f)

	with open('/var/log/syslog', 'w', encoding='utf-8') as f:
		events = [f"""\
			1970-01-01T00:00:00.000000-0000 THESE kernel: [    0.000000] usb 0-0: new high-speed USB device number 0 using ehci-pci
			1970-01-01T00:00:00.000000-0000 THESE kernel: [    0.000000] usb 0-0: New USB device found, idVendor=ARE, idProduct=JUST
			1970-01-01T00:00:00.000000-0000 THESE kernel: [    0.000000] usb 0-0: New USB device strings: Mfr=1, Product=2, SerialNumber=3
			1970-01-01T00:00:00.000000-0000 THESE kernel: [    0.000000] usb 0-0: Product: RANDOMLY
			1970-01-01T00:00:00.000000-0000 THESE kernel: [    0.000000] usb 0-0: Manufacturer: GENERATED
			1970-01-01T00:00:00.000000-0000 THESE kernel: [    0.000000] usb 0-0: SerialNumber: DEMO EVENTS
			1970-01-01T00:00:00.000000-0000 THESE kernel: [    0.000000] usb-storage 0-0: USB Mass Storage device detected
			1970-01-01T00:00:00.000000-0000 THESE kernel: [    0.000000] scsi host3: usb-storage 0-0
			1970-01-01T00:00:01.000000-0000 THESE kernel: [    0.000000] usb 0-0: USB disconnect, device number 0
		""".replace('\t', '')]

		for _ in range(10):
			connected = random_date(
				'1970-01-01T00:00:00',
				datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
				prop=random(),
				fmt='%Y-%m-%dT%H:%M:%S'
			)

			disconnected = date_offset(connected, fmt='%Y-%m-%dT%H:%M:%S')
			device_num = randint(1, 12)

			connected += '.000000-0000'
			host = 'usbrip'
			vid = str(randint(1, 9999)).rjust(4, '0')
			pid = str(randint(1, 9999)).rjust(4, '0')
			product = ''.join(choices(CHARSET, k=8))
			manufacturer = ''.join(choices(CHARSET, k=12))
			serial_number = ''.join(choices(CHARSET, k=13))
			port = randint(1, 3)
			disconnected += '.000000-0000'

			events.append(f"""\
				{connected} {host} kernel: [    0.000000] usb {port}-1: new high-speed USB device number {device_num} using ehci-pci
				{connected} {host} kernel: [    0.000000] usb {port}-1: New USB device found, idVendor={vid}, idProduct={pid}
				{connected} {host} kernel: [    0.000000] usb {port}-1: New USB device strings: Mfr=1, Product=2, SerialNumber=3
				{connected} {host} kernel: [    0.000000] usb {port}-1: Product: {product}
				{connected} {host} kernel: [    0.000000] usb {port}-1: Manufacturer: {manufacturer}
				{connected} {host} kernel: [    0.000000] usb {port}-1: SerialNumber: {serial_number}
				{connected} {host} kernel: [    0.000000] usb-storage {port}-1:1.0: USB Mass Storage device detected
				{connected} {host} kernel: [    0.000000] scsi host3: usb-storage {port}-1:1.0
				{disconnected} {host} kernel: [    0.000000] usb {port}-1: USB disconnect, device number {device_num}
			""".replace('\t', ''))

		events.sort(key=lambda x: datetime.strptime(x[:31], '%Y-%m-%dT%H:%M:%S.%f%z'))
		f.writelines(events)
