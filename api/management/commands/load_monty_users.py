import csv
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from registrations.models import UserExternalToken
from registrations.utils import jwt_encode_handler

logging = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates users and respective external token mentioned in the .csv file"
    missing_args_message = "Filename is missing. Filename / path to TAB separated CSV file required."

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    def handle(self, *args, **options):
        filename = options["filename"][0]
        with open(filename, newline="", encoding="utf-8") as csvfile:
            user_list = list(csv.DictReader(csvfile))

            for user_data in user_list:
                # Creating User using email
                user, _ = User.objects.get_or_create(username=user_data["e-mail address"], email=user_data["e-mail address"])
                user.is_superuser = False
                user.is_staff = False
                user.password = make_password(user_data["e-mail address"])
                user.save()

                # Save user profile
                profile = user.profile
                profile.limit_access_to_guest = True
                profile.save(update_fields=["limit_access_to_guest"])
                logging.info(f"User {user.username} created successfully")

                # Creating External Monty Token
                user_external_token = UserExternalToken(
                    title="CSV users Monty token",
                    user=user,
                    expire_timestamp=timezone.now() + timedelta(days=settings.JWT_EXPIRE_TIMESTAMP_DAYS),
                )
                token = jwt_encode_handler(user_external_token.get_payload())
                user_external_token.token = token
                user_external_token.save(update_fields=["token"])
                print(f"External Token for {user.username} is {token}")

        logging.info("All users created successfully")
