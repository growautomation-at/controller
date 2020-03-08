#!/usr/bin/python3
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
#ga_version0.3
import mysql.connector
from os import system as os_system
from subprocess import Popen as subprocess_popen
from subprocess import PIPE as subprocess_pipe
from functools import lru_cache

from ga.core import ant


def owlconfig(setting):
    return ga.core.config.get(setting, skipsql=True)


class do:
    def __init__(self, command, write=False, debug=False):
        self.command = command
        self.write = write
        self.fallback = False
        self.debug = debug
        self.prequesites()

    def connection(self, command=None):
        if self.fallback is True:
            conndata = "user=%s, passwd=%s" % (owlconfig("mysql_localuser"), owlconfig("mysql_localpwd"))
        else:
            conndata = "host=%s, port=%s, user=%s, passwd=%s" % (owlconfig("mysql.server_ip"), owlconfig("mysql.server_port"), owlconfig("mysql_user"), owlconfig("mysql_pwd"))
        connection = mysql.connector.connect(conndata)
        try:
            curser = connection.cursor(buffered=True)
            if command is None:
                command = self.command
            if self.write is False:
                @lru_cache()
                def readcache(doit):
                    curser.execute(doit)
                    return curser.fetchall()
                data = readcache(command)
            else:
                curser.execute(command)
                data = True
            curser.close()
            connection.close()
            return data
        except mysql.connector.Error as error:
            connection.rollback()
            ant.log("Mysql connection failed.\nCommand: %s\nError: %s" % (command, error))
            if self.fallback is True:
                ant.log("Server: %s, user %s" % ("127.0.0.1", owlconfig("mysql_localuser")))
            else:
                ant.log("Server: %s, port %s, user %s" % (owlconfig("mysql.server_ip"), owlconfig("mysql.server_port"), owlconfig("mysql_user")))
            print(error)
            return False

    def prequesites(self):
        creds_ok = False
        if owlconfig("setuptype") != "agent":
            def running():
                output, error = subprocess_popen(["systemctl status mysql.service | grep 'Active:'"],
                                                 shell=True, stdout=subprocess_pipe, stderr=subprocess_pipe).communicate()
                outputstr = output.decode("ascii")

                if outputstr.find("Active:") == -1:
                    return False
                elif outputstr.find("active (running)") != -1:
                    return True
                else:
                    return False
            whilecount = 0
            while True:
                if running() is False:
                    if whilecount == 0:
                        ant.log("Trying to start mysql service.")
                        os_system("systemctl start mysql.service %s" % ant.log_redirect)
                    else:
                        ant.log("Mysql service not running.")
                        raise SystemExit("Mysql service not active.")
                whilecount += 1
        whilecount = 0
        while creds_ok is False:
            if whilecount == 1 and owlconfig("setuptype") == "agent":
                ant.log("Failing over to local read-only database")
                self.fallback = True
            if self.fallback is True and self.write is True:
                ant.log("Error connecting to database. Write operations are not allowed to local fallback database. Check you sql server connection.")
                raise SystemExit("Error connecting to database. Write operations are not allowed to local fallback database. "
                                 "Check you sql server connection.")
            if whilecount > 2:
                ant.log("Error connecting to database. Check content of %ga_root/core/core.conf file for correct sql login credentials.")
                raise SystemExit("Error connecting to database. Check content of %ga_root/core/core.conf file for correct sql login credentials.")

            def conntest():
                if owlconfig("setuptype") == "agent":
                    table = "AgentConfig"
                else:
                    table = "ServerConfig"
                if self.write is False:
                    data = self.connection("SELECT * FROM ga.%s ORDER BY changed DESC LIMIT 10;" % table)
                else:
                    self.connection("INSERT INTO ga.AgentConfig (author, agent, setting, data) VALUES ('owl', '%s', 'conntest', 'ok');" % owlconfig("hostname"))
                    self.connection("DELETE FROM ga.AgentConfig WHERE author = 'owl' and agent = '%s';" % owlconfig("hostname"))
                    data = True
                if type(data) == list:
                    return True
                elif type(data) == bool:
                    return data
                else:
                    return False

            creds_ok = conntest()
            whilecount += 1
        self.execute()

    def execute(self):
        if type(self.command) == str:
            return self.connection()
        elif type(self.command) == list:
            outputdict = {}
            anyfalse = True
            forcount = 1
            for command in self.command:
                output = self.connection()
                if self.debug is True:
                    outputdict[forcount][command] = output
                else:
                    outputdict[forcount] = output
                if output is False:
                    anyfalse = False
                forcount += 1
            if anyfalse is False:
                return False
            return outputdict