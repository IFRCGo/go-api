import csv
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from registrations.models import UserExternalToken
from registrations.utils import jwt_encode_handler

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates users and respective external token mentioned in the .csv file"
    missing_args_message = "Filename is missing. Filename / path to TAB separated CSV file required."

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str, help="Path to the TAB separated CSV file")

    def handle(self, *args, **options):
        filename = options["filename"]
        try:
            with open(filename, newline="", encoding="utf-8") as csvfile:
                user_list = list(csv.DictReader(csvfile))

                for user_data in user_list:
                    self.create_user_with_token(user_data)
        except FileNotFoundError:
            logger.error(f"File {filename} not found.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    def create_user_with_token(self, user_data):
        email = user_data["e-mail address"]
        first_name, last_name = self.split_name(user_data["Name"])

        with transaction.atomic():
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={"first_name": first_name, "last_name": last_name, "email": email, "password": make_password(email)},
            )

            user.profile.limit_access_to_guest = True
            user.profile.save(update_fields=["limit_access_to_guest"])

            user_external_token = UserExternalToken(
                title="External user monty token",
                user=user,
                created_at=timezone.now(),
                expire_timestamp=timezone.now() + timedelta(days=settings.JWT_EXPIRE_TIMESTAMP_DAYS),
            )
            token = jwt_encode_handler(user_external_token.get_payload())
            self.stdout.write(self.style.SUCCESS(f"User: {user.username}, Monty Token: {token}"))

    @staticmethod
    def split_name(name):
        parts = name.split(" ", 1)
        first_name = parts[0].strip()
        last_name = parts[1].strip() if len(parts) > 1 else ""
        return first_name, last_name
