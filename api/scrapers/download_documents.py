import os
import json
import sys
import requests
import xmltodict
import logging

from utils import async_download, download_from_url

logger = logging.getLogger(__name__)

LIMIT = 5

HEADERS = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0'}

TYPES = (
    ('epoa', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=241&c=&co=&dt=1&f=2018&feed=appeals&re=&t=2018&ti=&zo='), # noqa
    ('ou', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=56&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
    ('fr', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=57&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
    ('ea', 'http://www.ifrc.org/Utils/Search/Rss.ashx?at=246&c=&co=&dt=1&feed=appeals&re=&ti=&zo='), # noqa
)

ERRORED_URLS = []


def exception_handler(exception, response=None, url=None, filename=None, retry=False):
    if not retry:
        ERRORED_URLS.append((url, filename))
    # logger.error(traceback.format_exc())
    logger.error(
        'Error for URL {} <- {}: {}'.format(
            str(url),
            exception.__class__.__name__,
            str(exception),
        ),
    )


def get_documents(cache_dir):
    ALREADY_DOWNLOADED = []

    def get_documents_for(url, d_type):
        response = requests.get(url)
        items = xmltodict.parse(response.content)['rss']['channel']['item']
        link_with_filenames = []
        for item in items:
            title = item.get('title')
            link = item.get('link')
            filename = os.path.join(
                cache_dir, 'pdf/{}/{}.pdf'.format(d_type, title)
            )
            if not os.path.isfile(filename):
                link_with_filenames.append([link, filename])
            else:
                ALREADY_DOWNLOADED.append([link, filename])
        return link_with_filenames

    url_with_filenames = []
    logger.info('Retrieving file list...')
    for d_type, url in TYPES:
        documents = get_documents_for(url, d_type)
        url_with_filenames.extend(documents)
    file_meta_path = os.path.join(cache_dir, 'file_meta.json')
    os.makedirs(os.path.dirname(file_meta_path), exist_ok=True)
    with open(file_meta_path, 'w') as fp:
        json.dump({
            '{}__{}'.format(
                filename.split('/')[-2], filename.split('/')[-1]
            ): link
            for link, filename in url_with_filenames + ALREADY_DOWNLOADED
        }, fp)

    already_downloaded_num = len(ALREADY_DOWNLOADED)
    total_num_docs = len(url_with_filenames) + len(ALREADY_DOWNLOADED)
    async_download(
        url_with_filenames,
        headers=HEADERS,
        exception_handler=exception_handler
    )

    errored_num_docs = len(ERRORED_URLS)
    logger.warn('{} Already Exsists, {} Success, {} Error downloading docs. {}'.format(
        already_downloaded_num, total_num_docs - errored_num_docs, errored_num_docs,
        ' Retrying....' if errored_num_docs else '',
    ))

    # Retry for errored urls using requests
    for url, filename in ERRORED_URLS:
        try:
            logger.info('Retrying for url {}'.format(url))
            download_from_url(url, filename, HEADERS)
            errored_num_docs -= 1
            logger.info('Success for url {}'.format(url))
        except Exception as e:
            exception_handler(e, url=url, retry=True)

    logger.warn('Total docs: {}'.format(total_num_docs))
    logger.warn('Already existing docs: {}'.format(already_downloaded_num))
    logger.warn('Success downloads: {}'.format(len(url_with_filenames)))
    logger.warn('Error downloads: {}'.format(errored_num_docs))
    logger.warn('Download Complete')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    get_documents(cache_dir='.cache')
