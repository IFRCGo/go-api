from datetime import datetime
from celery import shared_task
from playwright.sync_api import sync_playwright

from django.core.files.base import ContentFile
from django.utils import timezone

from api.models import Export
from .logger import logger


@shared_task
def generate_url(url, export_id, selector):
    export = Export.objects.filter(id=export_id).first()
    try:
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
            timeout = 1000000000
            page = browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
            )
            page.set_default_navigation_timeout(timeout)
            page.set_default_timeout(timeout)
            page.goto(url)
            if selector:
                page.wait_for_selector(selector, state="attached")
            file_name = f'dref-export-{datetime.now()}.pdf'
            file = ContentFile(page.pdf(format="A4"))
            browser.close()
        export.pdf_file.save(file_name, file)
        export.status = Export.ExportStatus.COMPLETED
        export.completed_at = timezone.now()
        export.save(update_fields=['status', 'completed_at'])
    except Exception as e:
        logger.error(e)
        export.status = Export.ExportStatus.ERRORED
        export.save(update_fields=['status'])
