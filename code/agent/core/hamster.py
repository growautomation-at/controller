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

# ga_version 0.4

from .owl import DoSql
from .config import GetConfig
from .ant import LogWrite
from .smallant import debugger

from inspect import getfile as inspect_getfile
from inspect import currentframe as inspect_currentframe

LogWrite("Current module: %s" % inspect_getfile(inspect_currentframe()), level=2)

# for agent only
# caching data if sql is not reachable (bad connection)
# timer to try to push cache to server db