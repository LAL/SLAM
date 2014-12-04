import os
import sys
sys.path.append("test/")
sys.path.append("src/")
os.environ["DJANGO_SETTINGS_MODULE"] = "webinterface.settings"

from django.core.management import call_command
from django.conf import settings


def setup():
    call_command("syncdb", interactive=False)


def teardown():
    os.unlink(settings.DATABASES["default"]["NAME"])
