# Officially a work of Navin (toggle-corp/ifrc), modified some parts for Django Admin usage
import os
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

from extractor import MetaFieldExtractor, SectorFieldExtractor
from config import (
    _mfd,
    _s,
    _sfd,
)
# from download_documents import get_documents as download_documents
# from common import json_preety, seconds_to_human_readable


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
    ('ou', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=56&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
    ('fr', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=57&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
    ('ea', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=246&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
)


# def exception_handler(exception, response=None, url=None, filename=None, retry=False):
#     if not retry:
#         ERRORED_URLS.append((url, filename))
#     # logger.error(traceback.format_exc())
#     logger.error(
#         'Error for URL {} <- {}: {}'.format(
#             str(url),
#             exception.__class__.__name__,
#             str(exception),
#         ),
#     )


def get_documents(epoa_list):
    # TODO: make this able to work with all types
    def get_documents_for(url, d_type):
        response = requests.get(url)
        items = xmltodict.parse(response.content)['rss']['channel']['item']
        link_with_filenames = []
        for item in items:
            # TODO: this looks through all types
            if item.get('link') and epoa_list.filter(raw_file_url=item.get('link')):
                title = item.get('title')
                link = item.get('link')
                filename = '{}.pdf'.format(title)

                link_with_filenames.append([link, filename])
        return link_with_filenames

    url_with_filenames = []
    # logger.info('Retrieving file list...')
    for d_type, url in TYPES:
        documents = get_documents_for(url, d_type)
        url_with_filenames.extend(documents)

    # Goes through the new PDFs
    for link in url_with_filenames:
        memoryfile = read_pdf_into_memory(link)

    # file_meta_path = os.path.join(cache_dir, 'file_meta.json')
    # os.makedirs(os.path.dirname(file_meta_path), exist_ok=True)
    # with open(file_meta_path, 'w') as fp:
    #     json.dump({
    #         '{}__{}'.format(
    #             filename.split('/')[-2], filename.split('/')[-1]
    #         ): link
    #         for link, filename in url_with_filenames + ALREADY_DOWNLOADED
    #     }, fp)

    # already_downloaded_num = len(ALREADY_DOWNLOADED)
    # total_num_docs = len(url_with_filenames) + len(ALREADY_DOWNLOADED)
    # async_download(
    #     url_with_filenames,
    #     headers=HEADERS,
    #     exception_handler=exception_handler
    # )

    # errored_num_docs = len(ERRORED_URLS)
    # logger.warn('{} Already Exsists, {} Success, {} Error downloading docs. {}'.format(
    #     already_downloaded_num, total_num_docs - errored_num_docs, errored_num_docs,
    #     ' Retrying....' if errored_num_docs else '',
    # ))

    # Retry for errored urls using requests
    # for url, filename in ERRORED_URLS:
    #     try:
    #         logger.info('Retrying for url {}'.format(url))
    #         download_from_url(url, filename, HEADERS)
    #         errored_num_docs -= 1
    #         logger.info('Success for url {}'.format(url))
    #     except Exception as e:
    #         exception_handler(e, url=url, retry=True)

    # logger.warn('Total docs: {}'.format(total_num_docs))
    # logger.warn('Already existing docs: {}'.format(already_downloaded_num))
    # logger.warn('Success downloads: {}'.format(len(url_with_filenames)))
    # logger.warn('Error downloads: {}'.format(errored_num_docs))
    # logger.warn('Download Complete')


def filter_not_processed_files(cache_dir, cached_data, directory, files):
    already_process_files = [
        '{}/pdf/{}/{}'.format(
            cache_dir,
            directory,
            output.get('filename'),
        ) for output in cached_data
    ]
    return len(already_process_files), [
        file for file in files if file not in already_process_files
    ]


def convert_pdf_to_text(file):
    readreport = PyPDF2.PdfFileReader(open(file, 'rb'))
    text = []
    for i in range(0, readreport.numPages):
        pageobj = readreport.getPage(i)
        text.append(pageobj.extractText())
    return ' '.join(text)


def convert_pdf_to_html(file):
    rsrcmgr = PDFResourceManager()
    with BytesIO() as retstr:
        laparams = LAParams()
        with HTMLConverter(
                rsrcmgr, retstr, codec='utf-8', laparams=laparams,
        ) as device:
            with open(file, 'rb') as fp:
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                maxpages = 0
                caching = True
                pagenos = set()
                for page in PDFPage.get_pages(
                        fp, pagenos, maxpages=maxpages,
                        caching=caching, check_extractable=True,
                ):
                    interpreter.process_page(page)

                text = retstr.getvalue().decode()
    html, errors = tidy_document(text)
    html = re.sub(r'\s\s+', ' ', html)
    text = convert_pdf_to_text(file)

    return html


def convert_pdf_to_text_blocks(file):
    html = convert_pdf_to_html(file)
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
    remoteFile = http.request('GET', url, headers=HEADERS)
    # memoryFile = BytesIO(remoteFile.content)

    return remoteFile
    # TODO: remoteFile vs memoryFile vs wtf happening
    # convert_pdf_to_text_blocks(remoteFile)
    # pdfFile = PyPDF2.PdfFileReader(open(memoryFile, 'rb'))


def start_extraction(epoa_list):
    # TODO: get already saved list from DB

    # TODO: get missing PDFs into memory

    # TODO: maybe need to close BytesIO stream after done with the files


    # FILES_DIR = os.path.join(cache_dir, 'pdf')
    # ERROR_FILES = []

    # output_js = os.path.join(output_dir, 'output.json')
    # output_js_with_score = os.path.join(output_dir, 'output_with_score.json')
    # OUTPUT = load_json_from_file(output_js) or {}
    # OUTPUT_WITH_SCORE = load_json_from_file(output_js_with_score) or {}

    # if download.lower() == 'true':
    #     download_documents(cache_dir=cache_dir)

    # with open(os.path.join(cache_dir, 'file_meta.json')) as fp:
    #     file_meta = json.load(fp)

    for directory, fields in pdf_types:
        # files = get_files_in_directory(os.path.join(FILES_DIR, directory))
        # OUTPUT[directory] = OUTPUT.get(directory, [])
        # OUTPUT_WITH_SCORE[directory] = OUTPUT_WITH_SCORE.get(directory, [])

        # if test.lower() == 'true':
        #     files = files[:5]
        # processed_file_len, unprocessed_files = filter_not_processed_files(
        #     cache_dir, OUTPUT[directory], directory, files,
        # )
        # print('Already processed for {} : {}'.format(directory, processed_file_len))
        # if len(unprocessed_files):
        #     print('Processing remaining docs for {}'.format(directory))
        for file in unprocessed_files:
            try:
                filename = file.split('/')[-1]

                texts = convert_pdf_to_text_blocks(file, cache_dir=cache_dir)
                m_texts = texts[:texts.index('Page 2')]
                m_extractor = MetaFieldExtractor(m_texts, fields)
                s_extractor = SectorFieldExtractor(texts, sectors, sector_fields)
                m_data_with_score, m_data = m_extractor.extract_fields()
                s_data_with_score, s_data = s_extractor.extract_fields()

                OUTPUT[directory].append({
                    'filename': file.split('/')[-1],
                    'url': file_meta.get('{}__{}'.format(directory, filename)),
                    'meta': m_data,
                    'sector': s_data,
                })
                OUTPUT_WITH_SCORE[directory].append({
                    'filename': file.split('/')[-1],
                    'url': file_meta.get('{}__{}'.format(directory, filename)),
                    'meta': m_data_with_score,
                    'sector': s_data_with_score,
                })

            except Exception as e:
                print('Proccess Failed!! {} (Error {}: {})'.format(
                    file, e.__class__.__name__, str(e),
                ))
                OUTPUT[directory].append({
                    'filename': file.split('/')[-1],
                    'url': file_meta.get('{}__{}'.format(directory, filename)),
                })
                OUTPUT_WITH_SCORE[directory].append({
                    'filename': file.split('/')[-1],
                    'url': file_meta.get('{}__{}'.format(directory, filename)),
                })
                ERROR_FILES.append(file)
            else:
                print('')

    # print('\nTotal Time: {}'.format(seconds_to_human_readable(time.time() - start)))
    # print('\n{0} ERROR FILES ({1}) {0}'.format('*' * 11, len(ERROR_FILES)))
    # [print('-> {}'.format(file)) for file in ERROR_FILES]

    # print('\n{0} SAVING {0}'.format('*' * 15))
    # os.makedirs(os.path.dirname(output_js), exist_ok=True)
    # os.makedirs(os.path.dirname(output_js_with_score), exist_ok=True)
    # with open(output_js, 'w') as fp:
    #     json.dump(OUTPUT, fp)
    #     print('Saved to {}'.format(output_js))
    # with open(output_js_with_score, 'w') as fp:
    #     json.dump(OUTPUT_WITH_SCORE, fp)
    #     print('Saved to {}'.format(output_js_with_score))

    for pdf_type, fields in pdf_types:
        output_filename = os.path.join(output_dir, 'csv/{}.csv').format(pdf_type)
        output_with_score_filename = os.path.join(
            output_dir,
            'csv/{}_with_score.csv'
        ).format(pdf_type)
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        os.makedirs(os.path.dirname(output_with_score_filename), exist_ok=True)
        output = json_normalize(OUTPUT.get(pdf_type))
        output.to_csv(output_filename)
        print('Saved to {}'.format(output_filename))

        output_with_score = json_normalize(OUTPUT_WITH_SCORE.get(pdf_type))
        output_with_score.to_csv(output_with_score_filename)
        print('Saved to {}'.format(output_with_score_filename))


if __name__ == '__main__':
    # import logging
    # import sys
    # logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    start_extraction()