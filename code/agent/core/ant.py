#!/usr/bin/python3.8
# This file is part of Growautomation
#     Copyright (C) 2020  René Pascal Rath
#
#     Growautomation is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#     E-Mail: rene.rath@growautomation.at
#     Web: https://git.growautomation.at

# ga_version 0.4

from smallconfig import Config

from datetime import datetime
from datetime import timedelta
from os import popen as os_popen
from os import system as os_system
from string import ascii_letters as string_ascii_letters
from string import digits as string_digits
from random import choice as random_choice
from colorama import Fore as colorama_fore
from getpass import getpass
# from functools import lru_cache


# Just vars
# log_redirect = " 2>&1 | tee -a %s" % Config("path_log").get()

# Time formats

def now(time_format):
    return datetime.now().strftime(time_format)


time01, time02, time03 = now("%H-%M-%S"), now("%H:%M:%S"), now("%H-%M")
date01, date02, date03, date04 = now("%Y-%m-%d"), now("%Y"), now("%m"), now("%d")
timestamp = "%Y-%m-%d %H:%M:%S"


class ShellInput:
    def __init__(self, prompt, default="", poss="", intype="", style="", posstype="", max_value=None, min_value=None, neg=False, lower=True):
        self.prompt, self.default, self.poss, self.intype, self.style = prompt, default, poss, intype, style
        self.posstype, self.max_value, self.min_value, self.neg, self.lower = posstype, max_value, min_value, neg, lower
        self.style_type, self.output = ShellOutput(style=style).colors(), ""
        self.lower, self.default_str, self.poss_str = "", "", ""

    def _string_check(self, to_check: str):
        if self.max_value is None: self.max_value = 20
        if self.min_value is None: self.min_value = 2
        to_check = str(to_check)
        char_blacklist = "!$§?^´`µ{}()><|\\*ÄÖÜüöä@,"
        if len(to_check) > self.max_value or len(to_check) < self.min_value:
            ShellOutput("Input error. Input must be between %s and %s characters long" % (self.min_value, self.max_value), style="warn", font="text")
            return False
        elif any((char in char_blacklist) for char in to_check):
            ShellOutput("Input error. Input must not include the following characters: %s" % char_blacklist, style="warn", font="text")
            return False
        else:
            return True

    def _poss_check(self):
        while_count = 0

        def _poss_error():
            if self.neg: ShellOutput("Input error. The following cannot be chosen: %s\n" % self.poss, style="warn", font="text")
            else: ShellOutput("Input error. Choose one of the following: %s\n" % self.poss, style="warn", font="text")
        while True:
            try:
                if while_count > 0: _poss_error()
                user_input = str(input(self.style_type + "\n%s%s%s%s%s\n > " %
                                       (self.prompt, self.poss_str, self.poss, self.default_str, self.default) +
                                       colorama_fore.RESET) or self.default)
                if self.posstype != "":
                    if self.posstype == "int": user_input = int(user_input)
                    elif self.posstype == "str": user_input = str(user_input)
                if type(self.poss) == list:
                    if user_input in self.poss: input_ok = True
                    else: input_ok = False
                else:
                    if user_input == self.poss: input_ok = True
                    else: input_ok = False
                if self.neg: input_ok = not input_ok
                if input_ok: break
            except (KeyError, ValueError): _poss_error()
            while_count += 1
        return user_input

    def get(self):
        if self.poss != "" or type(self.default) == bool:
            if self.neg: self.poss_str = "\nNo Poss: "
            else: self.poss_str = "\nPoss: "
        if self.default != "": self.default_str = "\nDefault: "
        if type(self.default) == bool:
            while True:
                try:
                    self.output = {"true": True, "false": False, "yes": True, "no": False, "y": True,
                                   "n": False, "f": False, "t": True, "": self.default}[
                        input(self.style_type + "\n%s%syes/no/true/false%s%s\n > " %
                              (self.prompt, self.poss_str, self.default_str, self.default) + colorama_fore.RESET)]
                    break
                except KeyError:
                    ShellOutput("WARNING: Invalid input please enter either yes/true/no/false!\n", style="warn", font="text")
            self.lower = False
        elif type(self.default) == str:
            if self.intype == "pass" and self.default != "":
                getpass(prompt="\n%s\nRandom: %s\n > " % (self.prompt, self.default)) or "%s" % self.default
            elif self.intype == "pass":
                getpass(prompt="\n%s\n > " % self.prompt)
            elif self.intype == "passgen":
                if self.max_value is None: self.max_value = 20
                if self.min_value is None: self.min_value = 8
                while True:
                    user_input = int(input("\n%s%s%s%s%s\n > " % (self.prompt, self.poss_str, self.poss, self.default_str,
                                                                  self.default)) or "%s" % self.default)
                    if user_input < int(self.min_value) or user_input > int(self.max_value):
                        ShellOutput("Input error. Value should be between %s and %s.\n" %
                                    (self.min_value, self.max_value), style="warn", font="text")
                    else: break
                self.output = user_input
            elif self.intype == "free" and self.poss == "":
                while True:
                    user_input = input(self.style_type + "\n%s%s%s\n > " % (self.prompt, self.default_str, self.default) +
                                       colorama_fore.RESET) or self.default
                    if self._string_check(user_input):
                        self.output = user_input
                        break
            elif self.poss != "": self.output = self._poss_check()
            else: self.output = input(self.style_type + "\n%s%s%s\n > " % (self.prompt, self.default_str, self.default) +
                                      colorama_fore.RESET) or "%s" % self.default
        elif type(self.default) == int:
            if self.min_value is None and self.max_value is None:
                self.max_value, self.min_value = 2592000, 1
            else:
                if self.max_value is None:
                    self.max_value = 2592000
                elif self.min_value is None:
                    self.min_value = 1
            while True:
                try: user_input = int(input("\n%s%s%s\n > " % (self.prompt, self.default_str, self.default)) or "%s" % self.default)
                except ValueError: user_input = 0
                if user_input < int(self.min_value) or user_input > int(self.max_value):
                    ShellOutput("Input error. Value should be between %s and %s." % (self.min_value, self.max_value), style="warn", font="text")
                else: break
            self.output, self.lower = user_input, False
        else: raise KeyError("Default value was neither str/int/bool | Value: '%s', '%s'" % (type(self.default), self.default))

        if self.lower is False: return self.output
        else: return self.output.lower()


# Shell output
class ShellOutput(object):
    def __init__(self, output=None, font="text", style="", symbol="#"):
        self.output, self.font,  self.style, self.symbol = output, font, style, symbol
        self.start()

    def start(self):
        self._header() if self.font == "head" else self._line if self.font == "line" \
            else self._text() if self.output is not None else None

    def _header(self):
        print("\n")
        self._line()
        print("%s" % self.output)
        self._line()
        print("\n")

    def colors(self):
        return colorama_fore.YELLOW if self.style == "warn" else colorama_fore.CYAN if self.style == "info" \
            else colorama_fore.RED if self.style == "err" \
            else colorama_fore.GREEN if self.style == "succ" else ""

    def _text(self):
        print(self.colors() + "%s\n" % self.output + colorama_fore.RESET)

    def _line(self):
        shellhight, shellwidth = os_popen('stty size', 'r').read().split()
        print(self.symbol * (int(shellwidth) - 1))


# File operations
class Line(object):
    def __init__(self, action, search, replace="", backup=False, file="./core.conf"):
        self.file, self.backup, self.searchfor, self.action, self.replacewith = file, backup, search, action, replace
        self.backupfile = "%s_%s_%s.bak" % (file, date01, time03)
        self.backupdir = "%s/%s" % (Config("path_backup").get(), date02)

    def __repr__(self):
        self.find() if self.action == "find" else self.delete() if self.action == "delete" else self.replace() if self.action == "replace" else self.add() if self.action == "add" else None

    def find(self):
        tmpfile = open(self.file, 'r')
        for xline in tmpfile.readlines(): return xline if xline.find(self.searchfor) != -1 else False

    def delete(self):
        os_system("sed -i%s '/%s/d' %s && mv %s %s %s" % (self.backupfile, self.searchfor, self.file, self.file, self.backupfile, self.backupdir)) if self.backup == "yes" \
            else os_system("sed -i '/%s/d' %s" % (self.searchfor, self.file))

    def replace(self):
        os_system("sed -i%s 's/%s/%s/p' %s && mv %s %s %s" % (self.backupfile, self.searchfor, self.replacewith, self.file, self.file, self.backupfile, self.backupdir)) if self.backup == "yes" \
            else os_system("sed -i 's/%s/%s/g' %s" % (self.searchfor, self.replacewith, self.file))

    def add(self):
        # insert after linenr / search = linenr
        os_system("sed -i%s '%s a %s' %s && mv %s %s %s" % (self.backupfile, self.searchfor, self.replacewith, self.file, self.file, self.backupfile, self.backupdir)) if self.backup == "yes" \
            else os_system("sed -i '%s a %s' %s" % (self.searchfor, self.replacewith, self.file))


def ga_setup_pwd_gen(stringlength):
    return ''.join(random_choice(string_ascii_letters + string_digits + "!#-_") for i in range(stringlength))


# Searches nested keys for values -> gives back the name of the nested keys
def dict_nested_search(dictionary, tosearch):
    return [(subkey if tosearch in subkey else None) for key in dictionary for subkey in dictionary[key]]


def string_check(string, maxlength=10, minlength=2):
    return False if type(string) != "str" else False if len(string) > maxlength or len(string) < minlength else False if any((char in "!%$§?^´`µ{}()°><|\\*ÄÖÜüöä@,") for char in string) else True


def dict_keycheck(dictionary, dictkey):
    return False if dictionary[dictkey] is None else True if dictkey in dictionary else False


def time_subtract(subtract, timeformat=timestamp, both=False):
    calculated = (datetime.now() - timedelta(seconds=subtract)).strftime(timeformat)
    return datetime.now().strftime(timeformat), calculated if both is True else calculated


def plural(data):
    def _base_check(nr):
        if nr > 1: return "s"
        else: return ""
    if type(data) == int: return _base_check(data)
    elif type(data) == list: return _base_check(len(data))
    elif type(data) == str:
        try:
            return _base_check(int(data))
        except ValueError:
            return ""
    else: return ""
