from sys import platform
from datetime import datetime
from pytz import timezone as pytz_timezone
from django.utils import timezone as django_timezone

from ..models import ObjectControllerModel
from ..models import ObjectInputModel, ObjectOutputModel, ObjectConnectionModel, GroupInputModel, GroupOutputModel, GroupConnectionModel
from ..models import MemberInputModel, MemberOutputModel, MemberConnectionModel
from ..subviews.handlers import handler404
from .process import subprocess


DEVICE_TYPES = [ObjectInputModel, ObjectOutputModel, ObjectConnectionModel]


def check_develop() -> bool:
    if platform == 'win32':
        return True

    else:
        return False


def get_time_difference(time_data: str, time_format: str) -> int:
    before = datetime.strptime(time_data, time_format)
    now = datetime.now()
    difference = now - before

    return int(difference.total_seconds())


def get_controller_setting(request, setting: str):
    try:
        controller = [cont for cont in ObjectControllerModel.objects.all()][0]
        return getattr(controller, setting)

    except IndexError:
        raise handler404(request, msg="Can't get controller setting if no controller exists. You must create a controller first.")


def get_script_dir(request, typ) -> str:
    path_root = get_controller_setting(request, setting='path_root')

    if platform == 'win32':
        output = "C:/Users/rene/Documents/code/ga/growautomation/code/device/%s" % typ.lower()
    else:
        output = "%s/device/%s/" % (path_root, typ.lower())

    return output


def get_client_ip(request):
    ip_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_forwarded:
        client_ip = ip_forwarded.split(',')[0]
    else:
        client_ip = request.META.get('REMOTE_ADDR')

    censored_client_ip = "%s.0" % client_ip.rsplit('.', 1)[0]

    return censored_client_ip


def develop_subprocess(command, develop: str = None) -> str:
    if check_develop():
        return develop

    return subprocess(command)


def add_timezone(request, datetime_obj):
    dt_w_tz = django_timezone.make_aware(datetime_obj, timezone=pytz_timezone(get_controller_setting(request, setting='timezone')))
    return dt_w_tz


def get_device_parent(child_obj):
    parent = None
    member_link_list = None

    if isinstance(child_obj, ObjectInputModel):
        member_link_list = MemberInputModel.objects.all()

    elif isinstance(child_obj, ObjectOutputModel):
        member_link_list = MemberOutputModel.objects.all()

    elif isinstance(child_obj, ObjectConnectionModel):
        member_link_list = MemberConnectionModel.objects.all()

    if member_link_list is not None:
        for link in member_link_list:
            if link.obj == child_obj:
                parent = link.group
                break

    return parent


def get_device_instance(obj: (str, int)):
    for typ in DEVICE_TYPES:
        for check_obj in typ.objects.all():
            if type(obj) == str:
                if check_obj.name == obj:
                    return check_obj
            else:
                if check_obj.id == obj:
                    return check_obj


def get_device_parent_setting(child_obj, setting: str):
    if type(child_obj) in [str, int]:
        child_obj = get_device_instance(obj=child_obj)

    parent = get_device_parent(child_obj)

    return getattr(parent, setting)
