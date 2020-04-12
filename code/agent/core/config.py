#!/usr/bin/python
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

# ga_version 0.3

from functools import lru_cache
from inspect import getfile as inspect_getfile
from inspect import currentframe as inspect_currentframe
from inspect import getframeinfo as inspect_getframeinfo

from ga.core.owl import DoSql
from ga.core.smallant import LogWrite
from ga.core.config_parser_file import GetConfig as parse_file

LogWrite("Current module: %s" % inspect_getfile(inspect_currentframe()), level=2)


class GetConfig(object):
    def __init__(self, setting=None, nosql=False, output=None, belonging=None, filter=None, table=None, debug=False):
        self.setting = setting
        self.nosql = nosql
        self.filter = filter
        self.belonging = belonging
        self.output = output
        self.table = table
        self.debug = debug

    def __repr__(self):
        parse_file_list = ["setuptype", "sql_pwd", "sql_local_user", "sql_local_pwd", "sql_agent_pwd", "sql_admin_pwd"]
        parse_failover_list = ["path_root", "hostname", "sql_server_port", "sql_server_ip", "sql_agent_user", "sql_admin_user",
                               "sql_server_port", "sql_sock"]
        output = parse_file() if self.setting in parse_file_list else self.parse_failover() if self.setting in parse_failover_list else self.parse_sql_custom() if self.nosql is False \
            else self.error("all")
        return self.error("sql") if output is False else str(output)

    def error(self, parser_type):
        if self.debug: print(inspect_getframeinfo(inspect_currentframe()).functiontype())
        LogWrite("%s parser could not find setting %s" % (parser_type.capitalize(), self.setting))
        raise SystemExit("%s parser could not find setting %s" % (parser_type.capitalize(), self.setting))

    @lru_cache()
    def parse_sql(self, command=None):
        if self.debug: print(inspect_getframeinfo(inspect_currentframe()).functiontype())
        response = DoSql(command, debug=self.debug) if command is not None else DoSql("SELECT data FROM ga.Setting WHERE setting = '%s' and belonging = '%s';"
                                                                                      % (self.setting, parse_file("hostname")), debug=self.debug)
        return self.error("sql") if response is False or response is None or response == "" else response

    @lru_cache()
    def parse_sql_custom(self):
        if self.debug: print(inspect_getframeinfo(inspect_currentframe()).functiontype())
        command, custom = ["SELECT", "data", "FROM ga.Setting WHERE"], False
        if self.table is not None:
            if self.table == "group":
                command = ["SELECT", "gid", "FROM ga.Grouping WHERE"]
            elif self.table == "object":
                command = ["SELECT", "type", "FROM ga.Object WHERE"]
            elif self.table == "data":
                command = ["SELECT", "data", "FROM ga.Data WHERE"]
        if self.output is not None:
            command[1], custom = self.output, True
        if self.setting is not None:
            if self.table is not None:
                if self.table == "group":
                    command.append("type = '%s'" % self.setting)
                elif self.table == "object":
                    command.append("name = '%s'" % self.setting)
                elif self.table == "data":
                    command.append("agent = '%s'" % self.setting)
            else: command.append("setting = '%s'" % self.setting)
            custom = True
        if self.belonging is not None:
            prefix = "AND" if self.setting is not None else ""
            if self.table is not None:
                if self.table == "group": insert = "member"
                elif self.table == "data": insert = "agent"
            else: insert = "belonging"
            command[3], custom = "%s %s = '%s'" % (prefix, insert, self.belonging), True
        if self.filter is not None:
            prefix = "AND " if self.setting is not None or self.belonging is not None else ""
            command.append("%s%s" % (prefix, self.filter))
            custom = True
        if self.debug: print("custom command:", type(custom), custom, "command:", type(command), command)
        return self.parse_sql(' '.join(command) + ";") if custom is True else self.parse_sql()

    @lru_cache()
    def parse_hardcoded(self):
        if self.debug: print(inspect_getframeinfo(inspect_currentframe()).functiontype())
        config_dict = {"path_log": "%s/log" % parse_file("path_root"), "path_backup": "%s/backup" % parse_file("path_root"), "sql_server_port": "3306"}
        if parse_file("setuptype") != "agent":
            config_server_dict = {"sql_server_ip": "127.0.0.1"}
            config_dict = {**config_dict, **config_server_dict}
        if self.setting in config_dict.keys():
            for key, value in config_dict.items():
                if key.find(self.setting) != -1:
                    if self.debug: print(type(key), key, type(value), value)
                    return value
            return False
        else:
            if self.debug: print("setting not found in hardcoded list")
            return False

    def parse_failover(self):
        if self.debug: print(inspect_getframeinfo(inspect_currentframe()).functiontype())
        parse_sql_output = self.parse_sql()
        if parse_sql_output is False or parse_sql_output is None or parse_sql_output == "" or self.nosql is True:
            parse_file_output = parse_file(self.setting)
            if parse_file_output is False or parse_file_output is None or parse_file_output == "":
                if self.parse_hardcoded() is False:
                    self.error("all")
                else:
                    output = self.parse_hardcoded()
                    if self.debug: print("output:", type(output), output)
                    return output
            else:
                if self.debug: print("output:", type(parse_file_output), parse_file_output)
                return parse_file_output
        else:
            output = self.parse_sql()
            if self.debug: print("output:", type(output), output)
            return output
