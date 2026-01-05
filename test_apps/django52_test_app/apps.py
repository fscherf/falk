import threading
import os

from django.apps import AppConfig
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth import get_user_model


class Config(AppConfig):
    name = "django52_test_app"

    def ready(self):

        # we need to run the initialization in a thread because Django will
        # otherwise complain about us being in the wrong context
        threading.Thread(
            target=self._initialize,
        ).start()

    def _initialize(self):

        # create database if not present
        sqlite_path = settings.DATABASES["default"]["NAME"]

        if not os.path.exists(sqlite_path):
            call_command("migrate", interactive=False)

        # create admin if non is present
        User = get_user_model()

        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="",
                password="admin",
            )
