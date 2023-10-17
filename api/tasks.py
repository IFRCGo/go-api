from datetime import datetime
import time
import pathlib
import tempfile
import json

from celery import shared_task
from playwright.sync_api import sync_playwright

from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

from api.models import Export
from .logger import logger
from rest_framework.authtoken.models import Token


def build_storage_state(tmp_dir, user, token):
    temp_file = pathlib.Path(tmp_dir, "storage_state.json")
    temp_file.touch()

    state = {
        "origins": [
            {
                "origin": 'https://' + settings.FRONTEND_URL + '/',
                "localStorage": [
                    {
                        "name": "user",
                        "value": json.dumps({
                            "id": user.id,
                            "username": user.username,
                            "firstName": user.first_name,
                            "lastName": user.last_name,
                            "token": token.key,
                        })
                    },
                    {
                        "name": "language",
                        "value": json.dumps("en")  # enforce all export to English
                    },
                ],
            }
        ]
    }
    with open(temp_file, "w") as f:
        json.dump(state, f)
    return temp_file


@shared_task
def generate_url(url, export_id, selector, user, title):
    export = Export.objects.filter(id=export_id).first()
    user = User.objects.filter(id=user).first()
    token = Token.objects.filter(user=user).last()
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--single-process",
                        "--no-zygote",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                    devtools=False,
                )
                storage_state = build_storage_state(
                    tmp_dir,
                    user,
                    token,
                )
                context = browser.new_context(
                    storage_state=storage_state
                )
                page = context.new_page()
                timeout = 300000
                page.goto(url, timeout=timeout)
                if selector:
                    time.sleep(5)
                    page.wait_for_selector(selector, state="attached", timeout=timeout)
                file_name = f'DREF {title} ({datetime.now().strftime("%Y-%m-%d %H-%M-%S")}).pdf'
                file = ContentFile(
                    page.pdf(
                        format="A4",
                        display_header_footer=True,
                        print_background=True,
                        footer_template="<div class=\"footer\" style=\"font-size: 8px;color: #fefefe; margin-left: 20px; position: relative; top: 10px;\">Page \
                        <span class=\"pageNumber\"></span> / <span class=\"totalPages\"></span>\
                        </div>\
                        ",
                    )
                )
                browser.close()
            export.pdf_file.save(file_name, file)
            export.status = Export.ExportStatus.COMPLETED
            export.completed_at = timezone.now()
            export.save(update_fields=['status', 'completed_at',])
    except Exception as e:
        logger.error(e)
        export.status = Export.ExportStatus.ERRORED
        export.save(update_fields=['status'])
