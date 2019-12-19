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
from io import BytesIO
from pandas.io.json import json_normalize
from bs4 import BeautifulSoup as bsoup
from pdfminer.converter import HTMLConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from tidylib import tidy_document

from api.scrapers.extractor import MetaFieldExtractor, SectorFieldExtractor
from .config import (
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
    _sfd.male, _sfd.female, _sfd.requirements, _sfd.people_targeted,
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

TYPES = (
    ('epoa', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=241&c=&co=&dt=1&f=2018&feed=appeals&re=&t=2018&ti=&zo='), # noqa
    # ('ou', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=56&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
    # ('fr', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=57&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
    # ('ea', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=246&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
)


def get_documents(epoa_list_in_db):
    def get_documents_for(url, d_type):
        response = requests.get(url)
        items = xmltodict.parse(response.content)['rss']['channel']['item']
        link_with_filenames = []
        for item in items:
            # TODO: this looks through all types, either change this part or make every one of them a separate function
            if item.get('link') and item.get('link') in epoa_list_in_db:
                title = item.get('title')
                link = item.get('link')
                filename = '{}.pdf'.format(title)

                link_with_filenames.append([link, filename])
        return link_with_filenames

    url_with_filenames = []

    for d_type, url in TYPES:
        documents = get_documents_for(url, d_type)
        url_with_filenames.extend(documents)

    return url_with_filenames


def convert_pdf_to_html(pdf_data):
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


def convert_pdf_to_text_blocks(pdf_data):
    html = convert_pdf_to_html(pdf_data)
    soup = bsoup(html, 'html.parser')
    texts = []
    for div in soup.find_all('div'):
        text = []
        for span in div.find_all(['span', 'a']):
            text.append(' '.join(span.get_text().split()))
        texts.append(' '.join(text).strip())

    return texts


def read_pdf_into_memory(url):
    http = urllib3.PoolManager()
    response = http.request('GET', url, headers=HEADERS)
    pdf_data = BytesIO(response.data)

    return pdf_data


# TODO: pass the queryset from the DB to this
def start_extraction(epoa_list_in_db):
    processed_data = []
    errored_data = []

    # Loop through the data types (epoa, ou, etc)
    for directory, fields in pdf_types:
        urls_with_filenames = get_documents(epoa_list_in_db)
        for doc in urls_with_filenames:
            try:
                pdf_data = read_pdf_into_memory(doc[0])
                texts = convert_pdf_to_text_blocks(pdf_data)
                m_texts = texts[:texts.index('Page 2')]
                m_extractor = MetaFieldExtractor(m_texts, fields)
                s_extractor = SectorFieldExtractor(texts, sectors, sector_fields)
                m_data_with_score, m_data = m_extractor.extract_fields()
                s_data_with_score, s_data = s_extractor.extract_fields()

                processed_data.append({
                    'url': doc[0],
                    'filename': doc[1],
                    'meta': m_data,
                    'sector': s_data
                })
            except Exception as e:
                # TODO: make a way to show failed PDFs somewhere

                errored_data.append({
                    'error': str(e)
                })
            else:
                print('')

    return processed_data