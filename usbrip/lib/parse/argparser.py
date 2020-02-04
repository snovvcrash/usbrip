#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""LICENSE

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
"""

__author__ = 'Sam Freeside (@snovvcrash)'
__email__  = 'snovvcrash@protonmail[.]ch'
__site__   = 'https://github.com/snovvcrash/usbrip'
__brief__  = 'Command line option parser'

import os
from pathlib import Path
from argparse import ArgumentParser

from usbrip.lib.core.usbstorage import USBStorage


def get_arg_parser():
    arg_parser = ArgumentParser()
    subparsers = arg_parser.add_subparsers(dest='subparser')

    # ----------------------------------------------------------
    # ------------------------- Banner -------------------------
    # ----------------------------------------------------------

    build_ub_parser(subparsers)

    # ----------------------------------------------------------
    # ----------------------- USB Events -----------------------
    # ----------------------------------------------------------

    build_ue_parser(subparsers)

    # ----------------------------------------------------------
    # ---------------------- USB Storage -----------------------
    # ----------------------------------------------------------

    build_us_parser(subparsers)

    # ----------------------------------------------------------
    # ------------------------ USB IDs -------------------------
    # ----------------------------------------------------------

    build_ui_parser(subparsers)

    return arg_parser


# ----------------------------------------------------------
# ------------------------- Banner -------------------------
# ----------------------------------------------------------


def build_ub_parser(subparsers):
    subparsers.add_parser(
        'banner',
        help='show tool banner'
    )


# ----------------------------------------------------------
# ----------------------- USB Events -----------------------
# ----------------------------------------------------------


def build_ue_parser(subparsers):
    ue_parser = subparsers.add_parser(
        'events',
        help='work with USB events'
    )

    ue_subparsers = ue_parser.add_subparsers(dest='ue_subparser')

    build_ueh_parser(ue_subparsers)
    build_ueo_parser(ue_subparsers)
    build_ueg_parser(ue_subparsers)
    build_uev_parser(ue_subparsers)


# ------------------- USB Events History -------------------


def build_ueh_parser(subparsers):
    ueh_parser = subparsers.add_parser(
        'history',
        help='show USB event history'
    )

    _parse_debug_args(ueh_parser)
    _parse_quiet_args(ueh_parser)
    _parse_column_args(ueh_parser)
    _parse_sieve_args(ueh_parser)
    _parse_repres_args(ueh_parser)
    _parse_file_args(ueh_parser)


# -------------------- USB Events Open ---------------------


def build_ueo_parser(subparsers):
    ueo_parser = subparsers.add_parser(
        'open',
        help='open USB event dump'
    )

    ueo_parser.add_argument(
        'input',
        type=str,
        help='input path for the event dump'
    )

    _parse_debug_args(ueo_parser)
    _parse_quiet_args(ueo_parser)
    _parse_column_args(ueo_parser)
    _parse_sieve_args(ueo_parser)
    _parse_repres_args(ueo_parser)
    _parse_file_args(ueo_parser)


# ------------------ USB Events GenAuth -------------------


def build_ueg_parser(subparsers):
    ueg_parser = subparsers.add_parser(
        'genauth',
        help='generate authorized device list (JSON)'
    )

    ueg_parser.add_argument(
        'output',
        type=str,
        nargs='?',
        default='/var/opt/usbrip/trusted/auth.json',
        help='output path for the list of authorized devices'
    )

    _parse_debug_args(ueg_parser)
    _parse_quiet_args(ueg_parser)
    _parse_sieve_args(ueg_parser)
    _parse_file_args(ueg_parser)

    _parse_attribute_args(
        ueg_parser,
        help_msg='attributes to include in authorized device list '
                 '(options: "vid", '
                 '"pid", '
                 '"prod", '
                 '"manufact", '
                 '"serial")'
    )


# ----------------- USB Events Violations ------------------


def build_uev_parser(subparsers):
    uev_parser = subparsers.add_parser(
        'violations',
        help='search USB event history for violations '
             '(show USB devices that do appear in hist'
             'ory and do NOT appear in authorized devi'
             'ce list)'
    )

    uev_parser.add_argument(
        'input',
        type=str,
        nargs='?',
        default='/var/opt/usbrip/trusted/auth.json',
        help='input path for the list of authorized devices'
    )

    _parse_debug_args(uev_parser)
    _parse_quiet_args(uev_parser)
    _parse_column_args(uev_parser)
    _parse_sieve_args(uev_parser)
    _parse_repres_args(uev_parser)
    _parse_file_args(uev_parser)

    _parse_attribute_args(
        uev_parser,
        help_msg='attributes to look through when searching for USB violation events '
                 '(options: "vid", '
                 '"pid", '
                 '"prod", '
                 '"manufact", '
                 '"serial")'
    )


# ----------------------------------------------------------
# ---------------------- USB Storage -----------------------
# ----------------------------------------------------------


def build_us_parser(subparsers):
    us_parser = subparsers.add_parser(
        'storage',
        help='work with USB event storage'
    )

    us_subparsers = us_parser.add_subparsers(dest='us_subparser')

    build_usl_parser(us_subparsers)
    build_uso_parser(us_subparsers)
    build_usu_parser(us_subparsers)
    build_usc_parser(us_subparsers)
    build_usp_parser(us_subparsers)


# -------------------- USB Storage List --------------------


def build_usl_parser(subparsers):
    usl_parser = subparsers.add_parser(
        'list',
        help='list storage contents'
    )

    _parse_debug_args(usl_parser)
    _parse_quiet_args(usl_parser)
    _parse_storage_type_args(usl_parser)


# -------------------- USB Storage Open --------------------


def build_uso_parser(subparsers):
    uso_parser = subparsers.add_parser(
        'open',
        help='open storage contents'
    )

    _parse_debug_args(uso_parser)
    _parse_quiet_args(uso_parser)
    _parse_storage_type_args(uso_parser)
    _parse_column_args(uso_parser)
    _parse_sieve_args(uso_parser)
    _parse_repres_args(uso_parser)


# ------------------- USB Storage Update -------------------


def build_usu_parser(subparsers):
    usu_parser = subparsers.add_parser(
        'update',
        help='update current storage'
    )

    _parse_debug_args(usu_parser)
    _parse_quiet_args(usu_parser)
    _parse_storage_type_args(usu_parser)
    _parse_comperssion_level_args(usu_parser)
    _parse_sieve_args(usu_parser)

    _parse_attribute_args(
        usu_parser,
        help_msg='attributes to look through when searching for USB violation events '
                 '(options: "vid", '
                 '"pid", '
                 '"prod", '
                 '"manufact", '
                 '"serial")'
    )

    usu_parser.add_argument(
        'input',
        type=str,
        nargs='?',
        default='/var/opt/usbrip/trusted/auth.json',
        help='input path for the list of authorized devices'
    )


# ------------------- USB Storage Create -------------------


def build_usc_parser(subparsers):
    usc_parser = subparsers.add_parser(
        'create',
        help=f'create initial history/violations storage; '
             f'storage path is "{USBStorage._STORAGE_BASE}"'
    )

    _parse_debug_args(usc_parser)
    _parse_quiet_args(usc_parser)
    _parse_storage_type_args(usc_parser)
    _parse_comperssion_level_args(usc_parser)
    _parse_sieve_args(usc_parser)

    _parse_attribute_args(
        usc_parser,
        help_msg='attributes to look through when searching for USB violation events '
                 '(options: "vid", '
                 '"pid", '
                 '"prod", '
                 '"manufact", '
                 '"serial")'
    )

    usc_parser.add_argument(
        'input',
        type=str,
        nargs='?',
        default='/var/opt/usbrip/trusted/auth.json',
        help='input path for the list of authorized devices'
    )


# ------------------- USB Storage Passwd -------------------


def build_usp_parser(subparsers):
    usp_parser = subparsers.add_parser(
        'passwd',
        help='change storage password'
    )

    _parse_debug_args(usp_parser)
    _parse_quiet_args(usp_parser)
    _parse_storage_type_args(usp_parser)
    _parse_comperssion_level_args(usp_parser)


# ----------------------------------------------------------
# ------------------------ USB IDs -------------------------
# ----------------------------------------------------------


def build_ui_parser(subparsers):
    ui_parser = subparsers.add_parser(
        'ids',
        help='work with USB IDs'
    )

    ui_subparsers = ui_parser.add_subparsers(dest='ui_subparser')

    build_uis_parser(ui_subparsers)
    build_uid_parser(ui_subparsers)


# --------------------- USB IDs Search ---------------------


def build_uis_parser(subparsers):
    uis_parser = subparsers.add_parser(
        'search',
        help=f'search by VID and/or PID; '
             f'ids database path is "{os.path.abspath(str(Path.home()))}/.config/usbrip/usb.ids"'
    )

    _parse_debug_args(uis_parser)
    _parse_quiet_args(uis_parser)

    uis_parser.add_argument(
        '--vid',
        type=str,
        default=None,
        help='vendor ID'
    )

    uis_parser.add_argument(
        '--pid',
        type=str,
        default=None,
        help='product ID'
    )

    uis_parser.add_argument(
        '--offline',
        action='store_true',
        help='offline mode (no database download/update)'
    )


# -------------------- USB IDs Download --------------------


def build_uid_parser(subparsers):
    uid_parser = subparsers.add_parser(
        'download',
        help=f'download/update database; '
             f'ids database path is "{os.path.abspath(str(Path.home()))}/.config/usbrip/usb.ids"'
    )

    _parse_debug_args(uid_parser)
    _parse_quiet_args(uid_parser)


# ----------------------------------------------------------
# ----------------------- Utilities ------------------------
# ----------------------------------------------------------


def _parse_debug_args(parser):
    parser.add_argument(
        '--debug',
        action='store_true',
        help='DEBUG mode'
    )


def _parse_quiet_args(parser):
    parser.add_argument(
        '-q',
        '--quiet',
        action='store_true',
        help='supress banner, some info messages, '
             'time capture and user iteraction'
    )


def _parse_column_args(parser):
    parser.add_argument(
        '-c',
        '--column',
        nargs='+',
        type=str,
        default=[],
        help='columns to show (options: "conn", '
             '"host", '
             '"vid", '
             '"pid", '
             '"prod", '
             '"manufact", '
             '"serial", '
             '"port", '
             '"disconn")'
    )


def _parse_sieve_args(parser):
    parser.add_argument(
        '-e',
        '--external',
        action='store_true',
        help='show only those devices which have "disconnect" date'
    )

    parser.add_argument(
        '-n',
        '--number',
        type=int,
        default=-1,
        help='number of events to show'
    )

    parser.add_argument(
        '-d',
        '--date',
        nargs='+',
        type=str,
        default=[],
        help='filter by dates'
    )

    parser.add_argument(
        '--host',
        nargs='+',
        type=str,
        default=[],
        help='search by hostname'
    )

    parser.add_argument(
        '--vid',
        nargs='+',
        type=str,
        default=[],
        help='search by VIDs'
    )

    parser.add_argument(
        '--pid',
        nargs='+',
        type=str,
        default=[],
        help='search by PIDs'
    )

    parser.add_argument(
        '--prod',
        nargs='+',
        type=str,
        default=[],
        help='search by products'
    )

    parser.add_argument(
        '--manufact',
        nargs='+',
        type=str,
        default=[],
        help='search by manufacturers'
    )

    parser.add_argument(
        '--serial',
        nargs='+',
        type=str,
        default=[],
        help='search by serial numbers'
    )

    parser.add_argument(
        '--port',
        nargs='+',
        type=str,
        default=[],
        help='search by ports'
    )


def _parse_repres_args(parser):
    group_table_list = parser.add_mutually_exclusive_group()

    group_table_list.add_argument(
        '-t',
        '--table',
        action='store_true',
        help='represent as table (not list)'
    )

    group_table_list.add_argument(
        '-l',
        '--list',
        action='store_true',
        help='represent as list (not table)'
    )


def _parse_attribute_args(parser, *, help_msg):
    parser.add_argument(
        '-a',
        '--attribute',
        nargs='+',
        type=str,
        default=[],
        help=help_msg
    )


def _parse_storage_type_args(parser):
    parser.add_argument(
        'storage_type',
        type=str,
        help='storage type (options: "history", "violations")'
    )


def _parse_comperssion_level_args(parser):
    parser.add_argument(
        '--lvl',
        type=str,
        default='5',
        help='compression level (from 0 to 9, default is 0 = no compression)'
    )


def _parse_file_args(parser):
    parser.add_argument(
        '-f',
        '--file',
        nargs='+',
        type=str,
        default=[],
        help='obtain log from the outer files'
    )
