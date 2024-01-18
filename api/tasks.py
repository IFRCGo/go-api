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
                "origin": "https://" + settings.FRONTEND_URL + "/",
                "localStorage": [
                    {
                        "name": "user",
                        "value": json.dumps(
                            {
                                "id": user.id,
                                "username": user.username,
                                "firstName": user.first_name,
                                "lastName": user.last_name,
                                "token": token.key,
                            }
                        ),
                    },
                    {"name": "language", "value": json.dumps("en")},  # enforce all export to English
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
    footer_template = """
        <div class="footer" style="width: 100%;font-size: 8px;color: #FEFEFE; bottom: 10px; position: absolute;">
        <div style="float: left; margin-top: 10px; margin-left: 40px;">
            Page <span class="pageNumber"></span> / <span class="totalPages"></span>
        </div>
        <div style="float: right; margin-right: 40px;">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 89.652 89.654"
                height="32"
                width="32"
            >
            <path
                d="M50.284 18.637a5.14 5.14 0 00-5.136-5.135 5.139 5.139 0 00-5.135 5.135 5.141 5.141 0 005.135 5.138 5.146 5.146 0 005.136-5.138M28.416 63.032a5.143 5.143 0 00-5.138 5.138 5.14 5.14 0 005.138 5.133 5.14 5.14 0 005.136-5.133 5.143 5.143 0 00-5.136-5.138M45.151 34.057a7.021 7.021 0 00-7.02 7.025 7.02 7.02 0 0014.04 0 7.021 7.021 0 00-7.02-7.025M61.883 63.032a5.143 5.143 0 00-5.135 5.138 5.138 5.138 0 005.135 5.133 5.14 5.14 0 005.136-5.133 5.143 5.143 0 00-5.136-5.138"
                class="st1"
                fill="#F5333F"
            />
            <path
                d="M61.883 75.769c-4.19 0-7.601-3.41-7.601-7.602 0-2.32 1.05-4.4 2.696-5.794L49.726 50.26a10.205 10.205 0 01-4.575 1.085c-1.648 0-3.196-.397-4.577-1.085l-7.252 12.113a7.571 7.571 0 012.693 5.794c0 4.191-3.408 7.602-7.599 7.602-4.19 0-7.601-3.41-7.601-7.602 0-4.19 3.41-7.601 7.601-7.601.984 0 1.926.196 2.791.54l7.303-12.2a10.236 10.236 0 01-3.63-7.827c0-5.254 3.947-9.58 9.038-10.189v-4.762c-3.606-.59-6.368-3.72-6.368-7.49 0-4.192 3.41-7.602 7.601-7.602s7.599 3.41 7.599 7.601c0 3.77-2.762 6.9-6.366 7.49v4.763c5.093.611 9.038 4.935 9.038 10.19a10.23 10.23 0 01-3.633 7.826l7.306 12.2a7.544 7.544 0 012.791-.54c4.191 0 7.599 3.41 7.599 7.601s-3.41 7.602-7.602 7.602m-49.286-34.65c0-5.485 3.44-10.057 9.194-10.057 4.194 0 7.715 2.236 8.226 6.562h-3.281c-.32-2.524-2.524-3.818-4.945-3.818-4.117 0-5.834 3.627-5.834 7.313s1.717 7.313 5.834 7.313c3.44.056 5.32-2.016 5.376-5.268h-5.106v-2.556h8.173v10.11h-2.151l-.51-2.257c-1.803 2.043-3.44 2.715-5.78 2.715-5.754 0-9.196-4.57-9.196-10.057M44.826 0C20.07 0 0 20.069 0 44.828c0 24.755 20.071 44.826 44.826 44.826 24.757 0 44.826-20.071 44.826-44.826C89.652 20.068 69.582 0 44.826 0"
                class="st1"
                fill="#F5333F"
            />
             </svg>
        </div>
        </div>
    """
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
                context = browser.new_context(storage_state=storage_state)
                page = context.new_page()
                timeout = 300000
                page.goto(url, timeout=timeout)
                if selector:
                    time.sleep(5)
                    page.wait_for_selector(selector, state="attached", timeout=timeout)
                file_name = f'DREF {title} ({datetime.now().strftime("%Y-%m-%d %H-%M-%S")}).pdf'
                file = ContentFile(
                    page.pdf(
                        display_header_footer=True,
                        prefer_css_page_size=True,
                        print_background=True,
                        footer_template=footer_template,
                        header_template="<p></p>",
                    )
                )
                browser.close()
            export.pdf_file.save(file_name, file)
            export.status = Export.ExportStatus.COMPLETED
            export.completed_at = timezone.now()
            export.save(
                update_fields=[
                    "status",
                    "completed_at",
                ]
            )
    except Exception as e:
        logger.error(e)
        export.status = Export.ExportStatus.ERRORED
        export.save(update_fields=["status"])
