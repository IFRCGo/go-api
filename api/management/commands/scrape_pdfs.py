# Officially a work of Navin (toggle-corp/ifrc), modified some parts for Django Admin usage
import os
import re
import time
import json
import PyPDF2
import urllib3
import xmltodict
import asyncio
import aiohttp
import aiofiles
import requests
import api.scrapers.cleaners as cleaners
from io import BytesIO
from pandas.io.json import json_normalize
from bs4 import BeautifulSoup as bsoup
from pdfminer.converter import HTMLConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from tidylib import tidy_document

from api.models import EmergencyOperationsDataset, EmergencyOperationsPeopleReached, EmergencyOperationsEA, EmergencyOperationsFR, CronJob, CronJobStatus
from api.logger import logger
from django.core.management.base import BaseCommand
from api.scrapers.extractor import MetaFieldExtractor, SectorFieldExtractor
from api.scrapers.config import (
    _mfd,
    _s,
    _sfd,
)


sectors = [
    _s.health, _s.shelter, _s.livelihoods_and_basic_needs,
    _s.Water_sanitation_hygiene, _s.disaster_Risk_reduction,
    _s.protection_gender_inclusion, _s.migration,
]
sector_fields = [
    _sfd.male, _sfd.female, _sfd.requirements, _sfd.people_targeted, _sfd.people_reached
]

epoa_fields = [
    _mfd.appeal_number, _mfd.glide_number,
    _mfd.date_of_issue, _mfd.appeal_launch_date,
    _mfd.expected_time_frame, _mfd.expected_end_date,
    _mfd.category_allocated, _mfd.dref_allocated,
    _mfd.num_of_people_affected,
    _mfd.num_of_people_to_be_assisted,
]
ou_fields = [
    _mfd.glide_number,
    _mfd.appeal_number,
    _mfd.date_of_issue,
    _mfd.epoa_update_num,
    _mfd.time_frame_covered_by_update,
    _mfd.operation_start_date,
    _mfd.operation_timeframe,
]
fr_fields = [
    # DREF/Emergency Appeal/One internal Appeal Number:
    _mfd.appeal_number,  # Operation number: MDRxx…
    _mfd.date_of_issue,
    _mfd.glide_number,
    _mfd.date_of_disaster,
    _mfd.operation_start_date,
    _mfd.operation_end_date,
    _mfd.overall_operation_budget,
    _mfd.num_of_people_affected,
    _mfd.num_of_people_to_be_assisted,
    _mfd.num_of_partner_ns_involved,
    _mfd.num_of_other_partner_involved,
]
ea_fields = [
    _mfd.appeal_number,
    _mfd.glide_number,
    _mfd.num_of_people_to_be_assisted,
    _mfd.dref_allocated,
    _mfd.current_operation_budget,
    # _mfd.funding_gap,
    _mfd.appeal_launch_date,
    # _mfd.Revision number,
    _mfd.appeal_ends,
    # _mfd.Extended X months,
]

pdf_types = (
    ('epoa', epoa_fields),
    ('ou', ou_fields),
    ('fr', fr_fields),
    ('ea', ea_fields),
)

HEADERS = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'}

TYPE_URLS = {
    'epoa': 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=241&c=&co=&dt=1&f=2018&feed=appeals&re=&t=2020&ti=&zo=',
    'ou': 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=56&c=&co=&dt=1&feed=appeals&re=&ti=&zo=',
    'fr': 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=57&c=&co=&dt=1&feed=appeals&re=&ti=&zo=',
    'ea': 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=246&c=&co=&dt=1&feed=appeals&re=&ti=&zo=',
}


class Command(BaseCommand):
    help = 'Scrape data from PDFs (only which are not already in the database)'

    def get_documents(self, pdf_type):
        def get_documents_for(url, d_type, db_set):
            response = requests.get(url)
            if response.status_code != 200:
                body = { "name": "scrape_pdfs",
                    "message": 'Error scraping ' + pdf_type + ' PDF-s from ' + url + '. (' + str(response.status_code) + ')',
                    "status": CronJobStatus.ERRONEOUS }
                CronJob.sync_cron(body)
            items = xmltodict.parse(response.content)['rss']['channel']['item']
            link_with_filenames = []
            for item in items:
                if item.get('link') and item.get('link') not in db_set:
                    title = item.get('title')
                    link = item.get('link')
                    filename = '{}.pdf'.format(title)

                    link_with_filenames.append([link, filename, d_type])
            
            return link_with_filenames

        url_with_filenames = []
        db_set = []
        # Records from DB for each type
        if pdf_type == 'epoa': 
            db_set = EmergencyOperationsDataset.objects.all().values_list('raw_file_url', flat=True)
        elif pdf_type == 'ou':
            db_set = EmergencyOperationsPeopleReached.objects.all().values_list('raw_file_url', flat=True)
        elif pdf_type == 'fr':
            db_set = EmergencyOperationsFR.objects.all().values_list('raw_file_url', flat=True)
        elif pdf_type == 'ea':
            db_set = EmergencyOperationsEA.objects.all().values_list('raw_file_url', flat=True)

        return get_documents_for(TYPE_URLS[pdf_type], pdf_type, db_set)


    def convert_pdf_to_html(self, pdf_data):
        pdf_rm = PDFResourceManager()
        bytesio = BytesIO()
        laparams = LAParams()
        html_conv = HTMLConverter(pdf_rm, bytesio, codec='utf-8', laparams=laparams)
        pdf_intr = PDFPageInterpreter(pdf_rm, html_conv)

        for page in PDFPage.get_pages(pdf_data, set(), maxpages=0, caching=False, check_extractable=True):
            pdf_intr.process_page(page)

        text = bytesio.getvalue().decode()
        html, errors = tidy_document(text)
        html = re.sub(r'\s\s+', ' ', html)

        html_conv.close()
        bytesio.close()

        return html


    def convert_pdf_to_text_blocks(self, pdf_data):
        html = self.convert_pdf_to_html(pdf_data)
        soup = bsoup(html, 'html.parser')
        texts = []
        for div in soup.find_all('div'):
            text = []
            for span in div.find_all(['span', 'a']):
                text.append(' '.join(span.get_text().split()))
            texts.append(' '.join(text).strip())

        return texts


    def read_pdf_into_memory(self, url):
        http = urllib3.PoolManager()
        response = http.request('GET', url, headers=HEADERS)
        pdf_data = BytesIO(response.data)

        return pdf_data


    def clean_data_and_save(self, scraped_data):
        epoa_to_add = []
        ou_to_add = []
        fr_to_add = []
        ea_to_add = []

        for data in scraped_data:
            if data['d_type'] == 'epoa':
                new_epoa = EmergencyOperationsDataset(
                    raw_file_name=data['filename'],
                    raw_file_url=data['url'],
                    raw_appeal_launch_date=data['meta'].get(_mfd.appeal_launch_date),
                    raw_appeal_number=data['meta'].get(_mfd.appeal_number),
                    raw_category_allocated=data['meta'].get(_mfd.category_allocated),
                    raw_date_of_issue=data['meta'].get(_mfd.date_of_issue),
                    raw_dref_allocated=data['meta'].get(_mfd.dref_allocated),
                    raw_expected_end_date=data['meta'].get(_mfd.expected_end_date),
                    raw_expected_time_frame=data['meta'].get(_mfd.expected_time_frame),
                    raw_glide_number=data['meta'].get(_mfd.glide_number),
                    raw_num_of_people_affected=data['meta'].get(_mfd.num_of_people_affected),
                    raw_num_of_people_to_be_assisted=data['meta'].get(_mfd.num_of_people_to_be_assisted),
                    raw_disaster_risk_reduction_female=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.female),
                    raw_disaster_risk_reduction_male=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.male),
                    raw_disaster_risk_reduction_people_reached=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_reached),
                    raw_disaster_risk_reduction_people_targeted=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_targeted),
                    raw_disaster_risk_reduction_requirements=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.requirements),
                    raw_health_female=data['sector'].get(_s.health, {}).get(_sfd.female),
                    raw_health_male=data['sector'].get(_s.health, {}).get(_sfd.male),
                    raw_health_people_reached=data['sector'].get(_s.health, {}).get(_sfd.people_reached),
                    raw_health_people_targeted=data['sector'].get(_s.health, {}).get(_sfd.people_targeted),
                    raw_health_requirements=data['sector'].get(_s.health, {}).get(_sfd.requirements),
                    raw_livelihoods_and_basic_needs_female=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.female),
                    raw_livelihoods_and_basic_needs_male=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.male),
                    raw_livelihoods_and_basic_needs_people_reached=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_reached),
                    raw_livelihoods_and_basic_needs_people_targeted=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_targeted),
                    raw_livelihoods_and_basic_needs_requirements=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.requirements),
                    raw_migration_female=data['sector'].get(_s.migration, {}).get(_sfd.female),
                    raw_migration_male=data['sector'].get(_s.migration, {}).get(_sfd.male),
                    raw_migration_people_reached=data['sector'].get(_s.migration, {}).get(_sfd.people_reached),
                    raw_migration_people_targeted=data['sector'].get(_s.migration, {}).get(_sfd.people_targeted),
                    raw_migration_requirements=data['sector'].get(_s.migration, {}).get(_sfd.requirements),
                    raw_protection_gender_and_inclusion_female=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.female),
                    raw_protection_gender_and_inclusion_male=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.male),
                    raw_protection_gender_and_inclusion_people_reached=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_reached),
                    raw_protection_gender_and_inclusion_people_targeted=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_targeted),
                    raw_protection_gender_and_inclusion_requirements=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.requirements),
                    raw_shelter_female=data['sector'].get(_s.shelter, {}).get(_sfd.female),
                    raw_shelter_male=data['sector'].get(_s.shelter, {}).get(_sfd.male),
                    raw_shelter_people_reached=data['sector'].get(_s.shelter, {}).get(_sfd.people_reached),
                    raw_shelter_people_targeted=data['sector'].get(_s.shelter, {}).get(_sfd.people_targeted),
                    raw_shelter_requirements=data['sector'].get(_s.shelter, {}).get(_sfd.requirements),
                    raw_water_sanitation_and_hygiene_female=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.female),
                    raw_water_sanitation_and_hygiene_male=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.male),
                    raw_water_sanitation_and_hygiene_people_reached=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_reached),
                    raw_water_sanitation_and_hygiene_people_targeted=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_targeted),
                    raw_water_sanitation_and_hygiene_requirements=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.requirements),
                    raw_education_female=data['sector'].get('education', {}).get(_sfd.female),
                    raw_education_male=data['sector'].get('education', {}).get(_sfd.male),
                    raw_education_people_reached=data['sector'].get('education', {}).get(_sfd.people_reached),
                    raw_education_people_targeted=data['sector'].get('education', {}).get(_sfd.people_targeted),
                    raw_education_requirements=data['sector'].get('education', {}).get(_sfd.requirements),

                    # Cleaned data
                    file_name=data['filename'],
                    appeal_launch_date=cleaners.clean_date(data['meta'].get(_mfd.appeal_launch_date)),
                    appeal_number=cleaners.clean_appeal_code(data['meta'].get(_mfd.appeal_number)),
                    category_allocated=data['meta'].get(_mfd.category_allocated),
                    date_of_issue=cleaners.clean_date(data['meta'].get(_mfd.date_of_issue)),
                    dref_allocated=cleaners.clean_number(data['meta'].get(_mfd.dref_allocated)),
                    expected_end_date=cleaners.clean_date(data['meta'].get(_mfd.expected_end_date)),
                    expected_time_frame=cleaners.clean_number(data['meta'].get(_mfd.expected_time_frame)),
                    glide_number=data['meta'].get(_mfd.glide_number)[18:] if data['meta'].get(_mfd.glide_number) != None else None,
                    num_of_people_affected=cleaners.clean_number(data['meta'].get(_mfd.num_of_people_affected)),
                    num_of_people_to_be_assisted=cleaners.clean_number(data['meta'].get(_mfd.num_of_people_to_be_assisted)),
                    disaster_risk_reduction_female=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.female)),
                    disaster_risk_reduction_male=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.male)),
                    disaster_risk_reduction_people_reached=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_reached)),
                    disaster_risk_reduction_people_targeted=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_targeted)),
                    disaster_risk_reduction_requirements=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.requirements)),
                    health_female=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.female)),
                    health_male=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.male)),
                    health_people_reached=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.people_reached)),
                    health_people_targeted=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.people_targeted)),
                    health_requirements=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.requirements)),
                    livelihoods_and_basic_needs_female=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.female)),
                    livelihoods_and_basic_needs_male=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.male)),
                    livelihoods_and_basic_needs_people_reached=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_reached)),
                    livelihoods_and_basic_needs_people_targeted=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_targeted)),
                    livelihoods_and_basic_needs_requirements=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.requirements)),
                    migration_female=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.female)),
                    migration_male=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.male)),
                    migration_people_reached=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.people_reached)),
                    migration_people_targeted=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.people_targeted)),
                    migration_requirements=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.requirements)),
                    protection_gender_and_inclusion_female=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.female)),
                    protection_gender_and_inclusion_male=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.male)),
                    protection_gender_and_inclusion_people_reached=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_reached)),
                    protection_gender_and_inclusion_people_targeted=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_targeted)),
                    protection_gender_and_inclusion_requirements=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.requirements)),
                    shelter_female=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.female)),
                    shelter_male=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.male)),
                    shelter_people_reached=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.people_reached)),
                    shelter_people_targeted=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.people_targeted)),
                    shelter_requirements=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.requirements)),
                    water_sanitation_and_hygiene_female=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.female)),
                    water_sanitation_and_hygiene_male=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.male)),
                    water_sanitation_and_hygiene_people_reached=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_reached)),
                    water_sanitation_and_hygiene_people_targeted=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_targeted)),
                    water_sanitation_and_hygiene_requirements=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.requirements)),
                    education_female=cleaners.clean_number(data['sector'].get('education', {}).get(_sfd.female)),
                    education_male=cleaners.clean_number(data['sector'].get('education', {}).get(_sfd.male)),
                    education_people_reached=cleaners.clean_number(data['sector'].get('education', {}).get(_sfd.people_reached)),
                    education_people_targeted=cleaners.clean_number(data['sector'].get('education', {}).get(_sfd.people_targeted)),
                    education_requirements=cleaners.clean_number(data['sector'].get('education', {}).get(_sfd.requirements)),
                )
                epoa_to_add.append(new_epoa)
            elif data['d_type'] == 'ou':
                new_ou = EmergencyOperationsPeopleReached(
                    raw_file_name=data['filename'],
                    raw_file_url=data['url'],
                    raw_appeal_number=data['meta'].get(_mfd.appeal_number),
                    raw_date_of_issue=data['meta'].get(_mfd.date_of_issue),
                    raw_epoa_update_num=data['meta'].get(_mfd.epoa_update_num),
                    raw_glide_number=data['meta'].get(_mfd.glide_number),
                    raw_operation_start_date=data['meta'].get(_mfd.operation_start_date),
                    raw_operation_timeframe=data['meta'].get(_mfd.operation_timeframe),
                    raw_time_frame_covered_by_update=data['meta'].get(_mfd.time_frame_covered_by_update),
                    raw_disaster_risk_reduction_female=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.female),
                    raw_disaster_risk_reduction_male=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.male),
                    raw_disaster_risk_reduction_people_reached=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_reached),
                    raw_disaster_risk_reduction_requirements=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.requirements),
                    raw_health_female=data['sector'].get(_s.health, {}).get(_sfd.female),
                    raw_health_male=data['sector'].get(_s.health, {}).get(_sfd.male),
                    raw_health_people_reached=data['sector'].get(_s.health, {}).get(_sfd.people_reached),
                    raw_health_requirements=data['sector'].get(_s.health, {}).get(_sfd.requirements),
                    raw_livelihoods_and_basic_needs_female=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.female),
                    raw_livelihoods_and_basic_needs_male=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.male),
                    raw_livelihoods_and_basic_needs_people_reached=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_reached),
                    raw_livelihoods_and_basic_needs_requirements=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.requirements),
                    raw_migration_female=data['sector'].get(_s.migration, {}).get(_sfd.female),
                    raw_migration_male=data['sector'].get(_s.migration, {}).get(_sfd.male),
                    raw_migration_people_reached=data['sector'].get(_s.migration, {}).get(_sfd.people_reached),
                    raw_migration_requirements=data['sector'].get(_s.migration, {}).get(_sfd.requirements),
                    raw_protection_gender_and_inclusion_female=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.female),
                    raw_protection_gender_and_inclusion_male=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.male),
                    raw_protection_gender_and_inclusion_people_reached=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_reached),
                    raw_protection_gender_and_inclusion_requirements=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.requirements),
                    raw_shelter_female=data['sector'].get(_s.shelter, {}).get(_sfd.female),
                    raw_shelter_male=data['sector'].get(_s.shelter, {}).get(_sfd.male),
                    raw_shelter_people_reached=data['sector'].get(_s.shelter, {}).get(_sfd.people_reached),
                    raw_shelter_requirements=data['sector'].get(_s.shelter, {}).get(_sfd.requirements),
                    raw_water_sanitation_and_hygiene_female=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.female),
                    raw_water_sanitation_and_hygiene_male=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.male),
                    raw_water_sanitation_and_hygiene_people_reached=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_reached),
                    raw_water_sanitation_and_hygiene_requirements=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.requirements),

                    # Cleaned data
                    file_name=data['filename'],
                    appeal_number=cleaners.clean_appeal_code(data['meta'].get(_mfd.appeal_number)),
                    date_of_issue=cleaners.clean_date(data['meta'].get(_mfd.date_of_issue)),
                    epoa_update_num=cleaners.clean_number(data['meta'].get(_mfd.epoa_update_num)),
                    glide_number=data['meta'].get(_mfd.glide_number)[18:] if data['meta'].get(_mfd.glide_number) != None else None,
                    operation_start_date=cleaners.clean_date(data['meta'].get(_mfd.operation_start_date)),
                    operation_timeframe=data['meta'].get(_mfd.operation_timeframe),
                    time_frame_covered_by_update=data['meta'].get(_mfd.time_frame_covered_by_update),
                    disaster_risk_reduction_female=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.female)),
                    disaster_risk_reduction_male=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.male)),
                    disaster_risk_reduction_people_reached=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_reached)),
                    disaster_risk_reduction_requirements=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.requirements)),
                    health_female=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.female)),
                    health_male=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.male)),
                    health_people_reached=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.people_reached)),
                    health_requirements=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.requirements)),
                    livelihoods_and_basic_needs_female=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.female)),
                    livelihoods_and_basic_needs_male=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.male)),
                    livelihoods_and_basic_needs_people_reached=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_reached)),
                    livelihoods_and_basic_needs_requirements=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.requirements)),
                    migration_female=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.female)),
                    migration_male=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.male)),
                    migration_people_reached=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.people_reached)),
                    migration_requirements=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.requirements)),
                    protection_gender_and_inclusion_female=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.female)),
                    protection_gender_and_inclusion_male=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.male)),
                    protection_gender_and_inclusion_people_reached=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_reached)),
                    protection_gender_and_inclusion_requirements=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.requirements)),
                    shelter_female=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.female)),
                    shelter_male=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.male)),
                    shelter_people_reached=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.people_reached)),
                    shelter_requirements=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.requirements)),
                    water_sanitation_and_hygiene_female=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.female)),
                    water_sanitation_and_hygiene_male=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.male)),
                    water_sanitation_and_hygiene_people_reached=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_reached)),
                    water_sanitation_and_hygiene_requirements=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.requirements)),
                )
                ou_to_add.append(new_ou)
            elif data['d_type'] == 'fr':
                new_fr = EmergencyOperationsFR(
                    raw_file_name=data['filename'],
                    raw_file_url=data['url'],
                    raw_appeal_number=data['meta'].get(_mfd.appeal_number),
                    raw_date_of_disaster=data['meta'].get(_mfd.date_of_disaster),
                    raw_date_of_issue=data['meta'].get(_mfd.date_of_issue),
                    raw_glide_number=data['meta'].get(_mfd.glide_number),
                    raw_num_of_other_partner_involved=data['meta'].get(_mfd.num_of_other_partner_involved),
                    raw_num_of_partner_ns_involved=data['meta'].get(_mfd.num_of_partner_ns_involved),
                    raw_num_of_people_affected=data['meta'].get(_mfd.num_of_people_affected),
                    raw_num_of_people_to_be_assisted=data['meta'].get(_mfd.num_of_people_to_be_assisted),
                    raw_operation_end_date=data['meta'].get(_mfd.operation_end_date),
                    raw_operation_start_date=data['meta'].get(_mfd.operation_start_date),
                    raw_disaster_risk_reduction_female=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.female),
                    raw_disaster_risk_reduction_male=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.male),
                    raw_disaster_risk_reduction_people_reached=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_reached),
                    #raw_disaster_risk_reduction_people_targeted=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_targeted),
                    raw_disaster_risk_reduction_requirements=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.requirements),
                    raw_health_female=data['sector'].get(_s.health, {}).get(_sfd.female),
                    raw_health_male=data['sector'].get(_s.health, {}).get(_sfd.male),
                    raw_health_people_reached=data['sector'].get(_s.health, {}).get(_sfd.people_reached),
                    #raw_health_people_targeted=data['sector'].get(_s.health, {}).get(_sfd.people_targeted),
                    raw_health_requirements=data['sector'].get(_s.health, {}).get(_sfd.requirements),
                    raw_livelihoods_and_basic_needs_female=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.female),
                    raw_livelihoods_and_basic_needs_male=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.male),
                    raw_livelihoods_and_basic_needs_people_reached=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_reached),
                    #raw_livelihoods_and_basic_needs_people_targeted=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_targeted),
                    raw_livelihoods_and_basic_needs_requirements=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.requirements),
                    raw_migration_female=data['sector'].get(_s.migration, {}).get(_sfd.female),
                    raw_migration_male=data['sector'].get(_s.migration, {}).get(_sfd.male),
                    raw_migration_people_reached=data['sector'].get(_s.migration, {}).get(_sfd.people_reached),
                    #raw_migration_people_targeted=data['sector'].get(_s.migration, {}).get(_sfd.people_targeted),
                    raw_migration_requirements=data['sector'].get(_s.migration, {}).get(_sfd.requirements),
                    raw_protection_gender_and_inclusion_female=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.female),
                    raw_protection_gender_and_inclusion_male=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.male),
                    raw_protection_gender_and_inclusion_people_reached=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_reached),
                    #raw_protection_gender_and_inclusion_people_targeted=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_targeted),
                    raw_protection_gender_and_inclusion_requirements=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.requirements),
                    raw_shelter_female=data['sector'].get(_s.shelter, {}).get(_sfd.female),
                    raw_shelter_male=data['sector'].get(_s.shelter, {}).get(_sfd.male),
                    raw_shelter_people_reached=data['sector'].get(_s.shelter, {}).get(_sfd.people_reached),
                    #raw_shelter_people_targeted=data['sector'].get(_s.shelter, {}).get(_sfd.people_targeted),
                    raw_shelter_requirements=data['sector'].get(_s.shelter, {}).get(_sfd.requirements),
                    raw_water_sanitation_and_hygiene_female=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.female),
                    raw_water_sanitation_and_hygiene_male=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.male),
                    raw_water_sanitation_and_hygiene_people_reached=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_reached),
                    #raw_water_sanitation_and_hygiene_people_targeted=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_targeted),
                    raw_water_sanitation_and_hygiene_requirements=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.requirements),

                    # Cleaned data
                    file_name=data['filename'],
                    appeal_number=cleaners.clean_appeal_code(data['meta'].get(_mfd.appeal_number)),
                    date_of_disaster=cleaners.clean_date(data['meta'].get(_mfd.date_of_disaster)),
                    date_of_issue=cleaners.clean_date(data['meta'].get(_mfd.date_of_issue)),
                    glide_number=data['meta'].get(_mfd.glide_number)[18:] if data['meta'].get(_mfd.glide_number) != None else None,
                    num_of_other_partner_involved=data['meta'].get(_mfd.num_of_other_partner_involved),
                    num_of_partner_ns_involved=data['meta'].get(_mfd.num_of_partner_ns_involved),
                    num_of_people_affected=cleaners.clean_number(data['meta'].get(_mfd.num_of_people_affected)),
                    num_of_people_to_be_assisted=cleaners.clean_number(data['meta'].get(_mfd.num_of_people_to_be_assisted)),
                    operation_end_date=cleaners.clean_date(data['meta'].get(_mfd.operation_end_date)),
                    operation_start_date=cleaners.clean_date(data['meta'].get(_mfd.operation_start_date)),
                    disaster_risk_reduction_female=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.female)),
                    disaster_risk_reduction_male=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.male)),
                    disaster_risk_reduction_people_reached=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_reached)),
                    #disaster_risk_reduction_people_targeted=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_targeted)),
                    disaster_risk_reduction_requirements=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.requirements)),
                    health_female=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.female)),
                    health_male=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.male)),
                    health_people_reached=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.people_reached)),
                    #health_people_targeted=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.people_targeted)),
                    health_requirements=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.requirements)),
                    livelihoods_and_basic_needs_female=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.female)),
                    livelihoods_and_basic_needs_male=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.male)),
                    livelihoods_and_basic_needs_people_reached=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_reached)),
                    #livelihoods_and_basic_needs_people_targeted=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_targeted)),
                    livelihoods_and_basic_needs_requirements=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.requirements)),
                    migration_female=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.female)),
                    migration_male=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.male)),
                    migration_people_reached=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.people_reached)),
                    #migration_people_targeted=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.people_targeted)),
                    migration_requirements=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.requirements)),
                    protection_gender_and_inclusion_female=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.female)),
                    protection_gender_and_inclusion_male=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.male)),
                    protection_gender_and_inclusion_people_reached=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_reached)),
                    #protection_gender_and_inclusion_people_targeted=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_targeted)),
                    protection_gender_and_inclusion_requirements=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.requirements)),
                    shelter_female=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.female)),
                    shelter_male=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.male)),
                    shelter_people_reached=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.people_reached)),
                    #shelter_people_targeted=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.people_targeted)),
                    shelter_requirements=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.requirements)),
                    water_sanitation_and_hygiene_female=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.female)),
                    water_sanitation_and_hygiene_male=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.male)),
                    water_sanitation_and_hygiene_people_reached=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_reached)),
                    #water_sanitation_and_hygiene_people_targeted=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_targeted)),
                    water_sanitation_and_hygiene_requirements=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.requirements)),
                )
                fr_to_add.append(new_fr)
            elif data['d_type'] == 'ea':
                new_ea = EmergencyOperationsEA(
                    raw_file_name=data['filename'],
                    raw_file_url=data['url'],
                    raw_appeal_ends=data['meta'].get(_mfd.appeal_ends),
                    raw_appeal_launch_date=data['meta'].get(_mfd.appeal_launch_date),
                    raw_appeal_number=data['meta'].get(_mfd.appeal_number),
                    raw_current_operation_budget=data['meta'].get(_mfd.current_operation_budget),
                    raw_dref_allocated=data['meta'].get(_mfd.dref_allocated),
                    raw_glide_number=data['meta'].get(_mfd.glide_number),
                    raw_num_of_people_to_be_assisted=data['meta'].get(_mfd.num_of_people_to_be_assisted),
                    raw_disaster_risk_reduction_female=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.female),
                    raw_disaster_risk_reduction_male=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.male),
                    raw_disaster_risk_reduction_people_reached=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_reached),
                    raw_disaster_risk_reduction_people_targeted=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_targeted),
                    raw_disaster_risk_reduction_requirements=data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.requirements),
                    raw_health_female=data['sector'].get(_s.health, {}).get(_sfd.female),
                    raw_health_male=data['sector'].get(_s.health, {}).get(_sfd.male),
                    raw_health_people_reached=data['sector'].get(_s.health, {}).get(_sfd.people_reached),
                    raw_health_people_targeted=data['sector'].get(_s.health, {}).get(_sfd.people_targeted),
                    raw_health_requirements=data['sector'].get(_s.health, {}).get(_sfd.requirements),
                    raw_livelihoods_and_basic_needs_female=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.female),
                    raw_livelihoods_and_basic_needs_male=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.male),
                    raw_livelihoods_and_basic_needs_people_reached=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_reached),
                    raw_livelihoods_and_basic_needs_people_targeted=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_targeted),
                    raw_livelihoods_and_basic_needs_requirements=data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.requirements),
                    raw_migration_female=data['sector'].get(_s.migration, {}).get(_sfd.female),
                    raw_migration_male=data['sector'].get(_s.migration, {}).get(_sfd.male),
                    raw_migration_people_reached=data['sector'].get(_s.migration, {}).get(_sfd.people_reached),
                    raw_migration_people_targeted=data['sector'].get(_s.migration, {}).get(_sfd.people_targeted),
                    raw_migration_requirements=data['sector'].get(_s.migration, {}).get(_sfd.requirements),
                    raw_protection_gender_and_inclusion_female=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.female),
                    raw_protection_gender_and_inclusion_male=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.male),
                    raw_protection_gender_and_inclusion_people_reached=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_reached),
                    raw_protection_gender_and_inclusion_people_targeted=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_targeted),
                    raw_protection_gender_and_inclusion_requirements=data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.requirements),
                    raw_shelter_female=data['sector'].get(_s.shelter, {}).get(_sfd.female),
                    raw_shelter_male=data['sector'].get(_s.shelter, {}).get(_sfd.male),
                    raw_shelter_people_reached=data['sector'].get(_s.shelter, {}).get(_sfd.people_reached),
                    raw_shelter_people_targeted=data['sector'].get(_s.shelter, {}).get(_sfd.people_targeted),
                    raw_shelter_requirements=data['sector'].get(_s.shelter, {}).get(_sfd.requirements),
                    raw_water_sanitation_and_hygiene_female=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.female),
                    raw_water_sanitation_and_hygiene_male=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.male),
                    raw_water_sanitation_and_hygiene_people_reached=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_reached),
                    raw_water_sanitation_and_hygiene_people_targeted=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_targeted),
                    raw_water_sanitation_and_hygiene_requirements=data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.requirements),

                    # Cleaned data
                    file_name=data['filename'],
                    appeal_ends=cleaners.clean_date(data['meta'].get(_mfd.appeal_ends)),
                    appeal_launch_date=cleaners.clean_date(data['meta'].get(_mfd.appeal_launch_date)),
                    appeal_number=cleaners.clean_appeal_code(data['meta'].get(_mfd.appeal_number)),
                    current_operation_budget=cleaners.clean_number(data['meta'].get(_mfd.current_operation_budget)),
                    dref_allocated=cleaners.clean_number(data['meta'].get(_mfd.dref_allocated)),
                    glide_number=data['meta'].get(_mfd.glide_number)[18:] if data['meta'].get(_mfd.glide_number) != None else None,
                    num_of_people_to_be_assisted=cleaners.clean_number(data['meta'].get(_mfd.num_of_people_to_be_assisted)),
                    disaster_risk_reduction_female=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.female)),
                    disaster_risk_reduction_male=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.male)),
                    disaster_risk_reduction_people_reached=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_reached)),
                    disaster_risk_reduction_people_targeted=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.people_targeted)),
                    disaster_risk_reduction_requirements=cleaners.clean_number(data['sector'].get(_s.disaster_Risk_reduction, {}).get(_sfd.requirements)),
                    health_female=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.female)),
                    health_male=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.male)),
                    health_people_reached=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.people_reached)),
                    health_people_targeted=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.people_targeted)),
                    health_requirements=cleaners.clean_number(data['sector'].get(_s.health, {}).get(_sfd.requirements)),
                    livelihoods_and_basic_needs_female=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.female)),
                    livelihoods_and_basic_needs_male=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.male)),
                    livelihoods_and_basic_needs_people_reached=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_reached)),
                    livelihoods_and_basic_needs_people_targeted=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.people_targeted)),
                    livelihoods_and_basic_needs_requirements=cleaners.clean_number(data['sector'].get(_s.livelihoods_and_basic_needs, {}).get(_sfd.requirements)),
                    migration_female=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.female)),
                    migration_male=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.male)),
                    migration_people_reached=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.people_reached)),
                    migration_people_targeted=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.people_targeted)),
                    migration_requirements=cleaners.clean_number(data['sector'].get(_s.migration, {}).get(_sfd.requirements)),
                    protection_gender_and_inclusion_female=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.female)),
                    protection_gender_and_inclusion_male=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.male)),
                    protection_gender_and_inclusion_people_reached=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_reached)),
                    protection_gender_and_inclusion_people_targeted=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.people_targeted)),
                    protection_gender_and_inclusion_requirements=cleaners.clean_number(data['sector'].get(_s.protection_gender_inclusion, {}).get(_sfd.requirements)),
                    shelter_female=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.female)),
                    shelter_male=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.male)),
                    shelter_people_reached=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.people_reached)),
                    shelter_people_targeted=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.people_targeted)),
                    shelter_requirements=cleaners.clean_number(data['sector'].get(_s.shelter, {}).get(_sfd.requirements)),
                    water_sanitation_and_hygiene_female=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.female)),
                    water_sanitation_and_hygiene_male=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.male)),
                    water_sanitation_and_hygiene_people_reached=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_reached)),
                    water_sanitation_and_hygiene_people_targeted=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.people_targeted)),
                    water_sanitation_and_hygiene_requirements=cleaners.clean_number(data['sector'].get(_s.Water_sanitation_hygiene, {}).get(_sfd.requirements)),
                )
                ea_to_add.append(new_ea)

        ## None of the records get inserted if any of them fails, but it would be faster this way
        # logger.info('Adding new EPoA records to DB (count: {})'.format(len(epoa_to_add)))
        # EmergencyOperationsDataset.objects.bulk_create(epoa_to_add)
        # logger.info('Adding new OU records to DB (count: {})'.format(len(ou_to_add)))
        # EmergencyOperationsPeopleReached.objects.bulk_create(ou_to_add)
        # logger.info('Adding new FR records to DB (count: {})'.format(len(fr_to_add)))
        # EmergencyOperationsFR.objects.bulk_create(fr_to_add)
        # logger.info('Adding new EA records to DB (count: {})'.format(len(ea_to_add)))
        # EmergencyOperationsEA.objects.bulk_create(ea_to_add)

        logger.info('Adding new EPoA records to DB (count: {})'.format(len(epoa_to_add)))
        for epoa_rec in epoa_to_add:
            try:
                epoa_rec.save()
            except:
                logger.error('Couldn\'t add EPoA: {fn} ({fu})'.format(fn=epoa_rec.raw_file_name, fu=epoa_rec.raw_file_url))
        logger.info('Adding new OU records to DB (count: {})'.format(len(ou_to_add)))
        for ou_rec in ou_to_add:
            try:
                ou_rec.save()
            except:
                logger.error('Couldn\'t add OU: {fn} ({fu})'.format(fn=ou_rec.raw_file_name, fu=ou_rec.raw_file_url))
        logger.info('Adding new FR records to DB (count: {})'.format(len(fr_to_add)))
        for fr_rec in fr_to_add:
            try:
                fr_rec.save()
            except:
                logger.error('Couldn\'t add FR: {fn} ({fu})'.format(fn=fr_rec.raw_file_name, fu=fr_rec.raw_file_url))
        logger.info('Adding new EA records to DB (count: {})'.format(len(ea_to_add)))
        for ea_rec in ea_to_add:
            try:
                ea_rec.save()
            except:
                logger.error('Couldn\'t add EA: {fn} ({fu})'.format(fn=ea_rec.raw_file_name, fu=ea_rec.raw_file_url))


    def handle(self, *args, **options):
        logger.info('Starting PDF scraping.')
        processed_data = []
        errored_data = []

        # Loop through the data types (epoa, ou, etc)
        for pdf_type, fields in pdf_types:
            logger.info('Getting document list.')
            urls_with_filenames = self.get_documents(pdf_type)
            logger.info('Count of new {pdftype} documents: {doc_count}'.format(pdftype=pdf_type, doc_count=len(urls_with_filenames)))
            logger.info('Starting to process PDFs.')
            error_count = 0
            for doc in urls_with_filenames:
                try:
                    pdf_data = self.read_pdf_into_memory(doc[0])
                    texts = self.convert_pdf_to_text_blocks(pdf_data)
                    m_texts = texts[:texts.index('Page 2')]
                    m_extractor = MetaFieldExtractor(m_texts, fields)
                    s_extractor = SectorFieldExtractor(texts, sectors, sector_fields)
                    m_data_with_score, m_data = m_extractor.extract_fields()
                    s_data_with_score, s_data = s_extractor.extract_fields()

                    processed_data.append({
                        'url': doc[0],
                        'filename': doc[1],
                        'meta': m_data,
                        'sector': s_data,
                        'd_type': doc[2],
                    })
                except Exception as e:
                    error_count += 1
                    errored_data.append(str(e))
            cron_body = { "name": "scrape_pdfs",
                "message": 'Done scraping ' + pdf_type + ' PDF-s',
                "num_result": len(urls_with_filenames) - error_count,
                "status": CronJobStatus.SUCCESSFUL }
            CronJob.sync_cron(cron_body)

        if len(errored_data) > 0:
            logger.error(errored_data)
        logger.info('Processing PDFs finished.')

        logger.info('Starting data-cleaning.')
        self.clean_data_and_save(processed_data)
        logger.info('Finished the PDF scraping.')
