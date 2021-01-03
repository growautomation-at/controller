from django import forms
from django.core.exceptions import ValidationError

from .models import *


LABEL_DICT = {
    'name': 'Name',
    'description': 'Description',
    'group': 'Group',
    'obj': 'Object',
    'condition': 'Condition match',
    'link': 'Condition link',
    'nested_group': 'Nested group',
    'condition_group': 'Condition',
    'script': 'Script',
    'script_arg': 'Script argument',
    'script_bin': 'Script binary',
    'reverse': 'Reverse action',
    'reverse_type': 'Reverse type',
    'reverse_type_data': 'Reverse after',
    'reverse_script': 'Reverse script',
    'reverse_script_arg': 'Reverse script argument',
    'reverse_script_bin': 'Reverse script binary',
    'unit': 'Data unit',
    'datatype': 'Data type',
    'data': 'Data',
    'connection': 'Connection',
    'downlink': 'Downlink device',
    'value': 'Value',
    'operator': 'Operator',
    'check': 'Check type',
    'period': 'Period type',
    'period_data': 'Period',
    'special': 'Is special',
    'path_root': 'GA root path',
    'path_log': 'GA log path',
    'backup': 'Enable backup',
    'path_backup': 'GA backup path',
    'sql_server': 'SQL server',
    'sql_port': 'SQL server port',
    'sql_user': 'SQL user',
    'sql_secret': 'SQL password',
    'sql_database': 'SQL database',
    'log_level': 'Log level',
    'security': 'Security mode',
    'timezone': 'Timezone',
    'debug': 'Debug mode',
    'timer': 'Timer',
    'web_cdn': 'Use CDN',
    'web_warn': 'Hide warnings',
    'chart_type': 'Chart type',
    'time_format_min': 'Time minute format',
    'time_format_hour': 'Time hour format',
    'time_format_day': 'Time day format',
    'time_format_month': 'Time month format',
    'chart_x_max_ticks': 'x-Axis max ticks',
    'chart_y_max_suggest': 'y-Axis max suggest',
    'options_json': 'Chart.js options in json format',
    'input_device': 'Input device',
    'input_model': 'Input model',
    'area': 'Area',
    'start_ts': 'Start timestamp',
    'stop_ts': 'Stop timestamp',
    'chart_fill': 'Fill chart',
    'chart_fill_color': 'Chart fill color',
    'chart_border_color': 'Chart border color',
    'chart_border_width': 'Chart border width',
    'chart_point_radius': 'Chart point radius',
    'chart_point_color': 'Chart point color',
    'chart_point_type': 'Chart point type',
}

HELP_DICT = {
    'name': 'Name of the object or group [max length 50]',
    'description': 'Description of the object or group [can be empty, max length 255]',
    'group': 'Group to link',
    'obj': 'Object to link',
    'condition': 'Condition object to link',
    'link': 'Condition link to link to',
    'nested_group': 'Nested group to link',
    'condition_group': 'Condition to link',
    'script': 'Script to run for object [max length 50]',
    'script_arg': 'Script argument to pass when started [can be empty, max length 255]',
    'script_bin': 'Script binary to use to run the script [max length 100]',
    'reverse': 'If the action needs to be reversed actively',
    'reverse_type': 'How to reverse the action [can be empty]',
    'reverse_type_data': 'When to reverse the action [can be empty]',
    'reverse_script': 'Script to run when reversing the action (if empty -> the normal script will be run) [can be empty, max length 50]',
    'reverse_script_arg': 'Script argument to pass when reversing the action (if empty -> the normal script argument will be used) [can be empty, max length 255]',
    'reverse_script_bin': 'Script binary to use to run the script when reversing the action (if empty -> the normal script binary will be used) [can be empty, max length 100]',
    'unit': 'Unit of data (p.e. %, RH) [can be empty, max length 15]',
    'datatype': 'Type of data received from the input script [max length 50]',
    # 'data': 'Data',
    'connection': 'Connection port (p.e. GPIO or downlink pin) [max length 50]',
    'downlink': 'Downlink device (needed if p.e. analog to digital conversion is done via an intermediate device) [can be empty]',
    'value': 'Value to compare the input data to [max length 50]',
    'operator': 'Operator used for comparison',
    'check': 'Method used to calculate the comparison data from the datapool',
    'period': 'Method used to retrieve datapoints for the datapool',
    'period_data': 'Used in combination with the period type in the data retrieval process',
    'special': 'Generic special flag',
    'path_root': 'Path to the growautomation core installation [max length 255]',
    'path_log': 'Path for growautomation log creation [max length 255]',
    'backup': 'Should the integrated backup task be enabled?',
    'path_backup': 'Target path for backups -> if enabled [max length 255]',
    'sql_server': 'IP/Hostname of the SQL server (mariadb/mysql) that should be used [max length 50]',
    'sql_port': 'SQL server port to connect to [1-65535]',
    'sql_user': 'SQL user used for connecting to the sql server [max length 50]',
    'sql_secret': 'Password for the SQL user [max length 100]',
    'sql_database': 'SQL database that should be used [max length 50]',
    'log_level': 'How detailed should the logs be?',
    'security': 'If the advanced security mode should be enabled',
    'timezone': 'Timezone used for conditions and core [max length 50]',
    'debug': 'If the debug mode should be enabled',
    'timer': 'Interval (in seconds) to execute the device script or system task',
    'interval': 'Custom interval in which to execute system task',
    'web_cdn': 'If the webinterface should use css and javascript files from content delivery networks',
    'web_warn': 'If the webinterface should hide warnings',
    'chart_type': 'Chart.js chart-type',
    'time_format_min': 'Time format if the range is shown in minutes [must be valid moment.js format]',
    'time_format_hour': 'Time format if the range is shown in hours [must be valid moment.js format]',
    'time_format_day': 'Time format if the range is shown in days [must be valid moment.js format]',
    'time_format_month': 'Time format if the range is shown in months [must be valid moment.js format]',
    'chart_x_max_ticks': 'Maximum labels shown on x-Axis',
    'chart_y_max_suggest': 'y-Axis upper limit should start with this value (else dynamic) [can be empty]',
    'options_json': 'Chart.js options in json format (will replace all others) [max length 4096, can be empty]',
    'chart_fill': 'If the chart should be filled [can be empty]',
    'chart_fill_color': 'Color to fill the chart with [max length 50, can be empty]',
    'chart_border_color': 'Color of the chart border [max length 50, can be empty]',
    'chart_border_width': 'Width of the chart border [can be empty]',
    'chart_point_radius': 'Radius of chart data points [can be empty]',
    'chart_point_color': 'Color of chart data points [max length 50, can be empty]',
    'chart_point_type': 'Type of chart data points [can be empty]',
}


# base ##############################

class BaseForm(forms.ModelForm):
    class Meta:
        abstract = True


# objects ##############################

class ObjectConnectionForm(BaseForm):
    class Meta:
        model = ObjectConnectionModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class ObjectInputForm(BaseForm):
    class Meta:
        model = ObjectInputModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class ObjectOutputForm(BaseForm):
    class Meta:
        model = ObjectOutputModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class ObjectConditionForm(BaseForm):
    class Meta:
        model = ObjectConditionModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class ObjectConditionLinkForm(BaseForm):
    class Meta:
        model = ObjectConditionLinkModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class ObjectControllerForm(BaseForm):
    class Meta:
        model = ObjectControllerModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT

        widgets = {
            'sql_secret': forms.PasswordInput(),
        }


class ObjectTimerForm(BaseForm):
    class Meta:
        model = ObjectTimerModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


# data ##############################

class ChartForm(BaseForm):
    class Meta:
        model = ChartModel
        fields = model.field_list
        help_texts = HELP_DICT
        labels = LABEL_DICT


class ChartDatasetForm(BaseForm):
    class Meta:
        model = ChartDatasetModel
        fields = model.field_list
        help_texts = HELP_DICT
        labels = LABEL_DICT

    def clean(self):
        data = super().clean()
        input_device = data.get("input_device")
        input_model = data.get("input_model")
        start_ts = data.get("start_ts")
        period = data.get("period")
        period_data = data.get("period_data")

        if input_device and input_model:
            raise ValidationError("One one of the two can be chosen: 'input_device', 'input_model'")

        if start_ts and period:
            raise ValidationError("One one of the two can be chosen: 'start_ts', 'period'")

        if period and not period_data:
            raise ValidationError("Period data must be defined when period is chosen!")


class ChartLinkForm(BaseForm):
    class Meta:
        model = ChartLinkModel
        fields = model.field_list
        help_texts = HELP_DICT
        labels = LABEL_DICT


# groups ##############################

class GroupConnectionForm(BaseForm):
    class Meta:
        model = GroupConnectionModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class GroupInputForm(BaseForm):
    class Meta:
        model = GroupInputModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class GroupOutputForm(BaseForm):
    class Meta:
        model = GroupOutputModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class GroupConditionForm(BaseForm):
    class Meta:
        model = GroupConditionModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class GroupAreaForm(BaseForm):
    class Meta:
        model = GroupAreaModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


# members ##############################

class MemberConnectionForm(BaseForm):
    class Meta:
        model = MemberConnectionModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class MemberInputForm(BaseForm):
    class Meta:
        model = MemberInputModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class MemberOutputForm(BaseForm):
    class Meta:
        model = MemberOutputModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class MemberConditionLinkForm(BaseForm):
    class Meta:
        model = MemberConditionLinkModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class MemberConditionForm(BaseForm):
    class Meta:
        model = MemberConditionModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class MemberConditionOutputForm(BaseForm):
    class Meta:
        model = MemberConditionOutputModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class MemberConditionOutputGroupForm(BaseForm):
    class Meta:
        model = MemberConditionOutputGroupModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class MemberAreaForm(BaseForm):
    class Meta:
        model = MemberAreaModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


class MemberConditionAreaGroupForm(BaseForm):
    class Meta:
        model = MemberConditionAreaGroupModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


# nested groups ##############################

class NestedAreaForm(BaseForm):
    class Meta:
        model = NestedAreaModel
        fields = model.field_list
        labels = LABEL_DICT
        help_texts = HELP_DICT


# system ##############################

class SystemScriptForm(forms.Form):
    script_name = forms.CharField(max_length=50)
    script_file = forms.FileField()
