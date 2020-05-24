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

try:
    from core.owl import DoSql
    from core.ant import ShellOutput
    from core.ant import ShellInput
    from core.smallant import Log
    from core.ant import plural
    from core.smallant import debugger
    from core.smallant import VarHandler
except (ImportError, ModuleNotFoundError):
    from owl import DoSql
    from ant import ShellOutput
    from ant import ShellInput
    from smallant import Log
    from ant import plural
    from smallant import debugger
    from smallant import VarHandler

from os import system as os_system
from sys import argv as sys_argv
from random import choice as random_choice
from sys import exc_info as sys_exc_info
import signal


def signal_handler(signum=None, stack=None):
    if debug: VarHandler().stop()
    try:
        raise SystemExit("Received signal %s - '%s'" % (signum, sys_exc_info()[0].__name__))
    except AttributeError:
        raise SystemExit("Received signal %s" % signum)


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


class Create:
    def __init__(self, setup_config_dict=None):
        self.object_dict, self.setting_dict, self.group_dict = {}, {}, {}
        self.current_dev_list, self.current_dt_dict, self.current_setting_dict, self.current_obj_list = [], {}, {}, []
        self.new_dt_dict, self.new_dev_list = {}, []
        self.object_downlink_list = []
        if setup_config_dict is not None:
            self.setup = True
            self.hostname = setup_config_dict['hostname']
            self.setuptype = setup_config_dict['setuptype']
        else:
            self.setup = False
            from core.config import Config
            self.Config = Config
            self.hostname = Config('hostname').get()
            self.setuptype = Config('setuptype').get()
        self.start()

    def start(self):
        # check if tmp_config_dump is currently in folder -> ask to load old config and try to import it into the db
        if self.setup:
            self.create_core()
            self.create_agent()
        else:
            self.current_obj_list = [name for name in self.Config(output='name', table='object').get()]
        if self.create_devicetype() is not False:
            for grouping, nested in self.object_dict.items():
                for name, typ in dict(nested).items():
                    self.new_dt_dict[name] = typ
                    self.current_obj_list.append(name)
                    if grouping == 'core' or grouping == 'agent': continue
                    self.current_dt_dict[name] = typ
        if self.setup is False:
            for name, typ in self.Config(output="name, class", filter="type = 'devicetype'", table='object').get():
                self.current_dt_dict[name] = typ

        if self.create_device() is not False:
            self.current_dev_list = [name for key, value in self.object_dict.items() if key == 'device'
                                     for nested in dict(value).values() for name in dict(nested).keys()]
            self.new_dev_list.extend(self.current_dev_list)
            self.current_obj_list.extend(self.current_dev_list)
            for obj, nested in self.setting_dict.items():
                for setting, data in dict(nested).items():
                    self.current_setting_dict[obj] = setting
        if self.setup is False:
            self.current_dev_list.extend(self.Config(output='name', filter="type = 'device'", table='object').get('list'))
            for setting, belonging in self.Config(output="setting,belonging").get():
                self.current_setting_dict[belonging] = setting

        self.create_custom_setting()
        self.create_group()
        self.write_config()

    def create_core(self):
        self.setting_dict = {'check': {'range': 10, 'function': 'parrot.py'}, 'backup': {'timer': 86400, 'function': 'backup.py'},
                             'sensor_master': {'function': 'snake.py'}}
        self.object_dict = {'core': {'check': 'NULL', 'backup': 'NULL', 'sensor_master': 'NULL', 'service': 'NULL'},
                            'agent': {self.hostname: 'NULL'}}

    def create_agent(self):
        agent_object_dict = {}
        # will manage the creation of all default settings of the controller
        # flag to overwrite/keep old config

    def create_devicetype(self):
        ShellOutput('Device Types', symbol='#', font='head')
        while_devicetype = ShellInput("Do you want to add devicetypes?\nInfo: must be created for every sensor/action/downlink "
                                      "hardware model; "
                                      "they provide per model configuration", True).get()
        if while_devicetype is False: return False
        dt_object_dict = {}
        # if self.setup is False:
        #     for name in self.Config(output='name', filter="type = 'devicetype'", table='object').get(): dt_exist_list.append(name)
        debugger("confint - create_devicetype |obj_exist_list '%s'" % self.current_obj_list)
        ShellOutput('Devicetypes', symbol='-', font='head')
        while while_devicetype:
            ShellOutput(symbol='-', font='line')
            name, setting_dict = ShellInput("Provide a unique name - at max 20 characters long.\n",
                                            default='AirHumidity', poss=self.current_obj_list, neg=True).get(), {}
            dt_object_dict[name] = ShellInput('Provide a type.', default='sensor', poss=['sensor', 'action', 'downlink']).get()
            if dt_object_dict[name] != 'downlink':
                if ShellInput("Are all devices of this type connected the same way?\nInfo: If all devices are connected "
                              "via gpio or downlink",
                              default=True).get() is True:
                    setting_dict['connection'] = ShellInput("Are they connected via downlink or directly?\n"
                                                            "Info: 'downlink' => pe. analog to serial converter, 'direct' => gpio pin",
                                                            default='direct', poss=['downlink', 'direct']).get()
                else: setting_dict['connection'] = 'specific'
            else: setting_dict['connection'] = 'direct'
            if setting_dict['connection'] != 'downlink':
                setting_dict['function'] = ShellInput("Which function should be started for the devicetype?\n"
                                                      "Info: just provide the name of the file; they must be placed in the ga %s folder" % dt_object_dict[name],
                                                      default="%s.py" % name, intype='free', max_value=50).get()
                setting_dict['function_arg'] = ShellInput("Provide system arguments to pass to the function -> if you need it.\n"
                                                          "Info: pe. if one function can provide data to multiple devicetypes",
                                                          intype='free', min_value=0, max_value=75).get()
            if dt_object_dict[name] == 'action':
                setting_dict['boomerang'] = ShellInput("Will this type need to reverse itself?\n"
                                                       "Info: pe. opener that needs to open/close", default=False).get()
                if setting_dict['boomerang']:
                    setting_dict['boomerang_type'] = ShellInput('How will the reverse be initiated?',
                                                                default='threshold', poss=['threshold', 'time']).get()
                    if setting_dict['boomerang_type'] == 'time':
                        setting_dict['boomerang_time'] = ShellInput('Provide the time after the action will be reversed.',
                                                                    default=1200, max_value=1209600, min_value=10).get()
                    reverse_function = ShellInput('Does reversing need an other function?', default=False).get()
                    if reverse_function:
                        setting_dict['boomerang_function'] = ShellInput('Provide the name of the function.',
                                                                        default="%s.py" % name, intype='free', max_value=50).get()
                        setting_dict['function_arg'] = ShellInput('Provide system arguments to pass to the reverse function -> '
                                                                  'if you need it.', intype='free', min_value=0, max_value=75).get()
            elif dt_object_dict[name] == 'sensor':
                setting_dict['timer'] = ShellInput('Provide the interval to run the function in seconds.',
                                                   default=600, max_value=1209600, min_value=10).get()
                setting_dict['unit'] = ShellInput('Provide the unit for the sensor input.', default='°C', intype='free').get()
                setting_dict['threshold_max'] = ShellInput("Provide a maximum threshold value for the sensor.\n"
                                                           "Info: if this value is exceeded the linked action(s) will be started",
                                                           default=26, max_value=1000000, min_value=1).get()
                setting_dict['threshold_optimal'] = ShellInput("Provide a optimal threshold value for the sensor.\n"
                                                               "Info: if this value is reached the linked action(s) will be reversed",
                                                               default=20, max_value=1000000, min_value=1).get()

                setting_dict['timer_check'] = ShellInput('How often should the threshold be checked? Interval in seconds.',
                                                         default=3600, max_value=1209600, min_value=60).get()
            elif dt_object_dict[name] == 'downlink':
                setting_dict['portcount'] = ShellInput('How many client-ports does this downlink provide?', default=4).get()
                setting_dict['output_per_port'] = ShellInput("Can the downlink output data per port basis?\n"
                                                             "(Or can it only output the data for all of its ports at once?)",
                                                             default=False).get()
            self.setting_dict[name] = setting_dict
            self.current_obj_list.append(name)
            debugger("confint - create_devicetype |settings '%s'" % setting_dict)
            while_devicetype = ShellInput('Want to add another devicetype?', default=True, style='info').get()
        self.object_dict['devicetype'] = dt_object_dict

    def create_device(self):
        ShellOutput('Devices', symbol='#', font='head')
        if ShellInput('Do you want to create devices?', default=True).get() is False: return False
        d_object_dict, d_dl_list = {}, []
        if self.setup is False:
            # for name in self.Config(output='name', filter="type = 'device'", table='object').get(): d_exist_list.append(name)
            for name, dt in self.Config(output="name,class", filter="type = 'device'", table='object').get():
                if self.Config(output='class', setting=dt, table='object').get() == 'downlink': d_dl_list.append(name)
        d_dl_list.append('notinlist')

        def to_create(to_ask, info):
            create, create_dict = ShellInput("Do you want to add a %s\nInfo: %s" % (to_ask, info), default=True).get(), {}
            current_new_dt_list = [name for name, typ in self.new_dt_dict.items() if typ == to_ask]
            while create:
                ShellOutput(symbol='-', font='line')
                try: default_name = random_choice(current_new_dt_list)
                except IndexError: default_name = random_choice([dt for dt, typ in self.current_dt_dict.items() if typ == to_ask])
                name, setting_dict = ShellInput('Provide a unique name - at max 20 characters long.', default="%s01" % default_name,
                                                intype='free', poss=self.current_obj_list, neg=True).get(), {}
                create_dict[name] = ShellInput('Provide its devicetype.', default=[dt for dt in list(self.current_dt_dict.keys())
                                                                                   if name.find(dt) != -1][0],
                                               poss=list(self.current_dt_dict.keys())).get()
                if to_ask != 'downlink':
                    if create_dict[name] in self.new_dt_dict.keys():
                        dt_conntype = [data for obj, nested in self.setting_dict.items() if obj == create_dict[name] for setting, data in dict(nested).items() if setting == 'connection'][0]
                    elif self.setup is False: dt_conntype = self.Config(setting='connection', belonging=create_dict[name]).get()
                    else: dt_conntype = 'specific'
                    debugger("confint - create_device |dt_conntype '%s'" % dt_conntype)
                    if dt_conntype != 'specific': setting_dict['connection'] = dt_conntype
                    else: setting_dict['connection'] = ShellInput("How is the device connected to the growautomation agent?\n"
                                                                  "Info: 'downlink' => pe. analog to serial converter, 'direct' => gpio pin",
                                                                  default='direct', poss=['downlink', 'direct']).get()

                    if setting_dict['connection'] == 'downlink':
                        setting_dict['downlink'] = ShellInput("Provide the name of the downlink to which the device is connected to.\n"
                                                              "Info: the downlink must also be added as device",
                                                              default=str(random_choice(d_dl_list)), poss=d_dl_list).get()
                        if setting_dict['downlink'] == 'notinlist':
                            setting_dict['downlink'] = ShellInput("Provide the exact name of the downlink-device to which this device is connected to.\n"
                                                                  "Info: You will need to add this downlink-device in the next run of this config_interface.\n"
                                                                  "Warning: If you misconfigure this connection the current %s will not work properly!" % to_ask,
                                                                  default='ads1115', intype='free').get()
                # check how many ports are already connected minus the max dl ports -> poss/no-poss
                setting_dict['port'] = ShellInput('Provide the portnumber to which the device is/will be connected.', intype='free', min_value=1).get()
                self.setting_dict[name] = setting_dict
                self.current_obj_list.append(name)
                debugger("confint - create_device |settings '%s'" % setting_dict)
                if to_ask == 'downlink': d_dl_list.append(name)
                create = ShellInput("Want to add another %s?" % to_ask, True, style='info').get()
            d_object_dict[to_ask] = create_dict

        def check_type(name):
            if len([dt for dt, typ in self.current_dt_dict.items() if typ == name]) > 0:
                return True
            else: return False

        if check_type('downlink'):
            ShellOutput('Downlinks', symbol='-', font='head')
            to_create('downlink', "if devices are not connected directly to the gpio pins you will probably need this one\n"
                                  "Check the documentation for further information: https://docs.growautomation.at")
        d_dl_list.remove('notinlist')
        self.object_downlink_list = d_dl_list
        if check_type('sensor'):
            ShellOutput('Sensors', symbol='-', font='head')
            to_create('sensor', 'any kind of device that provides data to growautomation')
        if check_type('action'):
            ShellOutput('Actions', symbol='-', font='head')
            to_create('action', 'any kind of device that should react if the linked thresholds are exceeded')
        self.object_dict['device'] = d_object_dict

    def create_custom_setting(self):
        ShellOutput('Custom Settings', symbol='#', font='head')

        def add_setting(object_name):
            def another():
                return ShellInput("Do you want to add another setting to the object %s" % object_name, default=False).get()
                # ValueError: too many values to unpack (expected 2)
            setting_exist_list = [setting for obj, nested in self.setting_dict.items() if obj == object_name
                                  for setting in dict(nested).keys()]
            if self.setup is False:
                setting_exist_list.extend(self.Config(output='setting', filter="belonging = '%s'" % object_name).get('list'))
            change_dict, setting_count, setting_dict = {}, 0, {}
            while True:
                setting = ShellInput("Provide the setting name.\nInfo: max 30 chars & cannot already exist.", poss=setting_exist_list,
                                     intype='free', neg=True, max_value=30).get()
                data = ShellInput("Provide the setting data.\nInfo: max 100 chars", intype='free', max_value=100, min_value=1).get()
                setting_dict[setting] = data
                if another() is False: break
            if object_name in self.setting_dict.keys():
                tmp_dict = {key: val for obj, nested in self.setting_dict.items() if obj == object_name for key, val in dict(nested)}
                debugger("confint - add_setting |merge settings '%s'" % tmp_dict)
                setting_dict.update(tmp_dict)
            debugger("confint - add_setting |settings '%s'" % setting_dict)
            self.setting_dict[object_name] = setting_dict

        if ShellInput('Do you want to add custom settings?', default=True).get() is False: return False
        while True:
            object_to_edit = ShellInput("Choose one of the listed objects to edit.\n\nDeviceTypes:\n%s\nDevices:\n%s\n"
                                        % (list(self.current_dt_dict.keys()), self.current_dev_list), poss=self.current_dev_list,
                                        default=random_choice(self.current_dev_list), intype='free').get()
            add_setting(object_to_edit)
            if ShellInput('Do you want to add settings to another object?', default=True).get() is False: break

    def create_group(self):
        ShellOutput('Groups', symbol='#', font='head')
        if ShellInput('Do you want to create groups?', default=True).get() is False: return False

        def to_create(to_ask, info, info_member):
            create_count, create_dict, posslist = 0, {}, []
            create = ShellInput("Do you want to add a %s?\nInfo: %s" % (to_ask, info), True).get()
            if to_ask == 'sector':
                posslist = self.current_dev_list
                [posslist.remove(dev) for dev in self.object_downlink_list]
            elif to_ask == 'sectorgroup':
                posslist = grp_sector_exist_list
            elif to_ask == 'link':
                posslist = dt_action_list
                posslist.extend(dt_sensor_list)
            debugger("confint - create_group |posslist '%s'" % posslist)
            while create:
                ShellOutput(symbol='-', font='line')
                member_list, current_posslist = [], posslist
                member_count, add_member = 0, True
                while add_member:
                    if member_count == 0: info = "\nInfo: %s" % info_member
                    else: info = ''
                    member_list.append(ShellInput("Provide a name for member %s%s." % (member_count + 1, info),
                                                  poss=current_posslist, default=str(random_choice(current_posslist)), intype='free').get())
                    member_count += 1
                    current_posslist = list(set(posslist) - set(member_list))
                    if member_count > 1:
                        if len(current_posslist) > 0:
                            add_member = ShellInput('Want to add another member?', default=True, style='info').get()
                        else: add_member = False
                desc = ShellInput("Add a unique description to the %s" % to_ask, max_value=50, min_value=2, neg=True, poss=grp_desc_exist_list).get()
                grp_desc_exist_list.append(desc)
                create_dict[create_count] = {desc: member_list}
                create_count += 1
                debugger("confint - create_group |members '%s'" % member_list)
                create = ShellInput("Want to add another %s?" % to_ask, default=True, style='info').get()
            return create_dict

        if self.setup is False:
            grp_desc_exist_list = self.Config(output='description', table='grp').get()
        else:
            grp_desc_exist_list = []

        ShellOutput('Sectors', symbol='-', font='head')
        self.group_dict['sector'] = to_create('sector', 'links objects which are in the same area', 'must match one device')

        grp_sector_exist_list = [desc for typ, nested in self.group_dict.items() if typ == 'sector'
                                 for nested_too in dict(nested).values() for desc in dict(nested_too).keys()]
        if self.setup is False:
            sector_exist_list = self.Config(output='description', filter="type = 'sector'", table='grp').get()
            grp_sector_exist_list.extend(sector_exist_list)
        if len(grp_sector_exist_list) > 1:
            ShellOutput('Sector groups', symbol='-', font='head')
            self.group_dict['sectorgroup'] = to_create('sectorgroup', "links sectors to areas (beds in field)", 'must match one sector')

        ShellOutput('Devicetype links', symbol='-', font='head')
        dt_action_list = [name for key, value in self.object_dict.items() if key == 'devicetype'
                          for name, typ in dict(value).items() if typ == 'action']
        if self.setup is False:
            dt_action_list.extend(self.Config(output='name', filter="type = 'devicetype' AND class = 'action'",
                                              table='object').get('list'))
        dt_sensor_list = [name for key, value in self.object_dict.items() if key == 'devicetype'
                          for name, typ in dict(value).items() if typ == 'sensor']
        if self.setup is False:
            dt_sensor_list.extend(self.Config(output='name', filter="type = 'devicetype' AND class = 'sensor'",
                                              table='object').get('list'))
        if len(dt_action_list) > 0 and len(dt_sensor_list) > 0:
            self.group_dict['link'] = to_create('link', "links action- and sensortypes\npe. earth humidity sensor with water pump",
                                                'must match one devicetype')

    def write_config(self):
        ShellOutput('Writing configuration to database', symbol='#', font='head')
        Log("Writing configuration to database:\n\nobjects: '%s'\nsettings: '%s'\ngroups: '%s'"
            % (self.object_dict, self.setting_dict, self.group_dict), level=3).write()
        if self.setup is not True:
            tmp_config_dump = "%s/maintenance/add_config.tmp" % self.Config('path_root').get()
            with open(tmp_config_dump, 'w') as tmp:
                tmp.write("%s\n%s\n%s" % (self.object_dict, self.setting_dict, self.group_dict))

        ShellOutput('Writing object configuration', font='text')
        DoSql("INSERT IGNORE INTO ga.ObjectReference (author,name) VALUES ('setup','%s');" % self.hostname, write=True).start()
        [DoSql("INSERT IGNORE INTO ga.Category (author,name) VALUES ('setup','%s');" % key, write=True).start()
         for key in self.object_dict.keys()]
        insert_count, error_count = 0, 0
        for object_type, packed_values in self.object_dict.items():
            def unpack_values(values, parent='NULL'):
                count, error_count = 0, 0
                for object_name, object_class in sorted(values.items()):
                    if object_class != 'NULL':
                        DoSql("INSERT IGNORE INTO ga.ObjectReference (author,name) VALUES ('setup','%s');" % object_class,
                              write=True).start()
                        object_class = "'%s'" % object_class
                    if parent != 'NULL' and parent.find("'") == -1:
                        parent = "'%s'" % parent
                    if DoSql("INSERT INTO ga.Object (author,name,parent,class,type) VALUES ('setup','%s',%s,%s,'%s');" %
                             (object_name, parent, object_class, object_type), write=True).start() is False: error_count += 1
                    else: count += 1
                return count, error_count
            if object_type == 'device':
                for subtype, packed_subvalues in packed_values.items():
                    _, _2 = unpack_values(packed_subvalues, self.hostname)
                    error_count, insert_count = _2 + error_count, _ + insert_count
            else:
                _, _2 = unpack_values(packed_values)
                error_count, insert_count = _2 + error_count, _ + insert_count
        ShellOutput("added %s object%s" % (insert_count, plural(insert_count)), style='info', font='text')
        if error_count > 0:
            ShellOutput("%s error%s while inserting" % (error_count, plural(error_count)), style='err')
            Log("%s error%s while inserting" % (error_count, plural(error_count))).write()

        ShellOutput('Writing object settings', font='text')
        insert_count, error_count = 0, 0
        for object_name, packed_values in self.setting_dict.items():
            if object_name in self.new_dev_list or object_name in self.new_dt_dict: packed_values['enabled'] = 1
            for setting, data in sorted(packed_values.items()):
                if data == '': pass
                elif type(data) == bool:
                    if data is True: data = 1
                    else: data = 0
                if DoSql("INSERT INTO ga.Setting (author,belonging,setting,data) VALUES ('setup','%s','%s','%s');"
                         % (object_name, setting, data), write=True).start() is False:
                    error_count += 1
                else: insert_count += 1
        ShellOutput("added %s object setting%s" % (insert_count, plural(insert_count)), style='info', font='text')
        if error_count > 0:
            ShellOutput("%s error%s while inserting" % (error_count, plural(error_count)), style='err')
            Log("%s error%s while inserting" % (error_count, plural(error_count))).write()

        ShellOutput('Writing group configuration', font='text')
        insert_count, member_count, error_count = 0, 0, 0
        for group_type, packed_values in self.group_dict.items():
            for group_id, also_packed_values in dict(packed_values).items():
                for group_desc, group_member_list in dict(also_packed_values).items():
                    DoSql("INSERT IGNORE INTO ga.Category (author,name) VALUES ('setup','%s')" % group_type, write=True).start()
                    if DoSql("INSERT INTO ga.Grp (author,type,description) VALUES ('setup','%s','%s');"
                             % (group_type, group_desc), write=True).start() is False:
                        error_count += 1
                    else: insert_count += 1
                    sql_gid = DoSql("SELECT id FROM ga.Grp WHERE author = 'setup' AND type = '%s' ORDER BY changed DESC LIMIT 1;" %
                                    group_type).start()
                    for member in sorted(group_member_list):
                        if group_type == 'sectorgroup':
                            sector_gid = DoSql("SELECT id FROM ga.Grp WHERE description = '%s';" % member).start()
                            DoSql("INSERT IGNORE INTO ga.Category (author,name) VALUES ('setup','group');", write=True).start()
                            if DoSql("INSERT INTO ga.Object (author,name,type,description) VALUES ('setup','group_%s','group','%s');"
                                     % (sector_gid, member), write=True).start() is False: error_count +=1
                            if DoSql("INSERT INTO ga.Member (author,gid,member,description) VALUES ('setup','%s','group_%s','%s');"
                                     % (sql_gid, sector_gid, member), write=True).start() is False: error_count += 1
                            else: member_count += 1
                        else:
                            if DoSql("INSERT INTO ga.Member (author,gid,member) VALUES ('setup','%s','%s');" % (sql_gid, member),
                                     write=True).start() is False: error_count += 1
                            else: member_count += 1
        ShellOutput("added %s group%s with a total of %s member%s" % (insert_count, plural(insert_count), member_count, plural(member_count)), style='info', font='text')
        if error_count > 0:
            ShellOutput("%s error%s while inserting" % (error_count, plural(error_count)), style='err')
            Log("%s error%s while inserting" % (error_count, plural(error_count))).write()

        if self.setup is not True: os_system("rm %s" % tmp_config_dump)


class Edit:
    def __init__(self, enabled_state=None):
        from core.config import Config
        self.Config, self.enabled_state = Config, enabled_state
        self.start()

    def start(self):
        object_list = ['exit']
        object_agent_list = self.Config(output='name', table='object', filter="type = 'agent'").get('list')
        object_dev_list = self.Config(output='name', table='object', filter="type = 'device'").get('list')
        object_dt_list = self.Config(output='name', table='object', filter="type = 'devicetype'").get('list')
        object_list.extend(object_dev_list)
        object_list.extend(object_agent_list)
        object_list.extend(object_dt_list)
        todo = 'edit' if self.enabled_state is None else self.enabled_state
        while True:
            object_to_edit = ShellInput("Choose one of the listed objects to edit or type 'exit'.\n\nAgents:\n%s\nDeviceTypes:\n%s\nDevices:\n%s\n"
                                        % (object_agent_list, object_dt_list, object_dev_list),
                                        poss=object_list, default=random_choice(object_list), intype='free').get()
            if object_to_edit == 'exit': return False
            if self.enabled_state is not None:
                self.edit_setting(object_to_edit, setting_name='enabled', setting_data=1 if self.enabled_state == 'enable' else 0)
            else:
                what_to_edit = ShellInput('Do you want to edit a object itself or its settings?', poss=['object', 'setting'], default='setting', intype='free').get()
                if what_to_edit == 'setting': self.edit_setting(object_to_edit)
                elif what_to_edit == 'object': self.edit_object(object_to_edit)
            if ShellInput('Do you want to %s another object?' % todo, default=True).get() is False: break

    def edit_setting(self, object_name, setting_name=None, setting_data=None):
        change_dict, setting_count, setting_error_count = {}, 0, 0
        if setting_name is not None and setting_data is not None:
            change_dict[setting_name] = setting_data
        else:
            setting_dict = {setting: data for setting, data in self.Config(output="setting,data", filter="belonging = '%s'" % object_name).get('list')}
            while True:
                setting = ShellInput('Choose the setting you want to edit.',
                                     poss=list(setting_dict.keys()), default=random_choice(list(setting_dict.keys())), intype='free').get()
                ShellOutput("\nIts current configuration: %s = %s" % (setting, [val for key, val in setting_dict.items() if key == setting][0]), style='info')
                data = ShellInput("Provide the new setting data.\n"
                                  "Warning: If you misconfigure any settings it may lead to unforeseen problems!",
                                  intype='free', max_value=100, min_value=1).get()
                change_dict[setting] = data
                if ShellInput("Do you want to edit another setting of the object %s" % object_name, default=True).get() is False: break
        for setting, data in change_dict.items():
            if DoSql("UPDATE ga.Setting SET data = '%s' WHERE belonging = '%s' AND setting = '%s';" % (data, object_name, setting),
                     write=True).start() is False:
                setting_error_count += 1
            else: setting_count += 1
        ShellOutput("added %s object setting%s" % (setting_count, plural(setting_count)), style='info', font='text')
        if setting_error_count > 0: ShellOutput("%s error%s while inserting" % (setting_error_count, plural(setting_error_count)), style='err')

    def edit_object(self, object_name):
        ShellOutput("This option isn't supported yet.")
        raise SystemExit
        # need to check dependencies -> add with new name and update settings+dependencies -> after that delete the old named obj


def show():
    from core.config import Config
    object_list = ['exit']
    object_agent_list = Config(output='name', table='object', filter="type = 'agent'").get('list')
    object_dev_list = Config(output='name', table='object', filter="type = 'device'").get('list')
    object_dt_list = Config(output='name', table='object', filter="type = 'devicetype'").get('list')
    object_list.extend(object_dev_list)
    object_list.extend(object_agent_list)
    object_list.extend(object_dt_list)
    while True:
        object_name = ShellInput("The following objects exist:\n\nAgents:\n%s\nDeviceTypes:\n%s\nDevices:\n%s\n\n"
                                 "Choose the one to show the settings of or type 'exit'."
                                 % (object_agent_list, object_dt_list, object_dev_list),
                                 poss=object_list, default=random_choice(object_list), intype='free').get()
        if object_name == 'exit': break
        setting_list = ["'%s' = '%s'" % (setting, data) for setting, data in Config(output="setting,data", #
                                                                                    filter="belonging = '%s'" % object_name).get()]
        ShellOutput("\n\nThe following settings exist for the object '%s':\n\n%s" % (object_name, ' | '.join(setting_list)))
        ShellOutput(font='line', symbol='-')
    return True


class Delete:
    def __init__(self):
        self.start()

    def start(self):
        ShellOutput("Deletion of objects isn't supported yet.")
        return False


def setup(setup_dict=None):
    if setup_dict is None:
        setup_dict = {}
        setup_dict['hostname'] = ShellInput(prompt='Provide the name of this growautomation host.', default='gacon01')
        setup_dict['setuptype'] = ShellInput(prompt="Setup as growautomation standalone, agent or server?\n"
                                                    "Agent and Server setup is disabled for now. It will become available after further testing!",
                                             poss='standalone', default='standalone')  # ['agent', 'standalone', 'server']
        setup_dict['path_root'] = ShellInput(prompt='Want to choose a custom install path?', default='/etc/growautomation')
        setup_dict['log_level'] = ShellInput(prompt='Want to change the log level?', default='1', poss=['0', '1', '2', '3', '4', '5'])
        setup_dict['backup'] = ShellInput('Want to enable backup?', default=True)
        setup_dict['path_backup'] = ShellInput(prompt='Want to choose a custom backup path?', default='/mnt/growautomation/backup/')
        setup_dict['path_log'] = ShellInput(prompt='Want to choose a custom log path?', default='/var/log/growautomation')
    return Create(setup_config_dict=setup_dict)


def choose():
    ShellOutput('Growautomation - config change module', font='head', symbol='#')
    count = 0
    while True:
        count += 1
        if count > 1: ShellOutput(font='line', symbol='#')
        mode = ShellInput("Choose how you want to modify growautomation objects or type 'exit'.",
                          poss=['show', 'add', 'edit', 'enable', 'disable', 'delete', 'exit', 'setup'],
                          default='show', intype='free').get()
        if mode == 'show': start = show()
        elif mode == 'add': start = Create()
        elif mode == 'edit': start = Edit()
        elif mode == 'enable': start = Edit(enabled_state='enable')
        elif mode == 'disable': start = Edit(enabled_state='disable')
        elif mode == 'delete': start = Delete()
        elif mode == 'setup': start = setup()
        elif mode == 'exit': exit()
        else: raise SystemExit('Encountered unknown error while choosing config mode.')
        if start is False: continue


def exit():
    ShellOutput('\n\nBye!\nIt was a pleasure to serve you!')
    raise SystemExit


if __name__ == '__main__':
    try:
        if sys_argv[2] == 'debug':
            debug = True
            VarHandler(name='debug', data=1).set()
        else:
            debug = False
    except (IndexError, NameError):
        debug = False
    choose()
