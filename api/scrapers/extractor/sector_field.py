import re
from fuzzywuzzy import fuzz
# from common import json_preety
from api.scrapers.config import (
    S_KEYS,
    SF_KEYS,
    # M_EXTRACTORS,
    # get_sector_misc_keys,
)


class SectorFieldExtractor():
    def __init__(self, texts, sectors, fields):
        self.texts = texts
        self.sectors = sectors
        self.fields = fields
        # self.misc_fields = get_sector_misc_keys(sectors, fields)
        self.sector_meta = {}
        self.field_meta = {}
        self.extracted = {}

    def pre_processing(self):
        """
        Search for sector name and field combination
        eg: Health male, Health female ....
        """
        for index, text in enumerate(self.texts):
            for sector in S_KEYS:
                for sector_key in S_KEYS[sector]:
                    for field in SF_KEYS:
                        for field_key in SF_KEYS[field]:
                            search = re.search(
                                '{} {}'.format(sector_key, field_key),
                                text, re.IGNORECASE
                            )
                            if search:
                                start, end = search.span()
                                if not self.sector_meta.get(sector_key):
                                    self.sector_meta[sector] = {
                                        'text_index': index,
                                        'text': text,
                                        'start_index': start,
                                        'end_index': end,
                                        'field': field,
                                        'score': 100,
                                    }
                                break
                        if self.sector_meta.get(sector_key):
                            break
                    if self.sector_meta.get(sector_key):
                        break

    def fuzzy_find_remainig_sectors(self):
        def _search(key):
            ratio = 0
            sector_meta = {}
            for text_index, text in enumerate(self.texts):
                texts = text.split()
                for field in SF_KEYS:
                    for field_key in SF_KEYS[field]:
                        search_text = '{} {}'.format(key, field_key).split()
                        search_text_n = len(search_text)
                        for index in range(0, len(texts) - search_text_n):
                            real_text = texts[index:index+search_text_n]
                            new_ratio = fuzz.partial_ratio(real_text, search_text)
                            if not new_ratio > ratio:
                                continue
                            try:
                                search = re.search(' '.join(real_text), text)
                                if search:
                                    start, end = search.span()
                                    ratio = new_ratio
                                    sector_meta = {
                                        'text_index': text_index,
                                        'text': text,
                                        'start_index': start,
                                        'end_index': end,
                                        'score': ratio,
                                        'real_text': real_text,
                                        'search_text': search_text,
                                    }
                            except re.error:
                                pass
            return sector_meta

        def search(key, sector_meta):
            new_sector_meta = _search(key)
            if new_sector_meta['score'] > sector_meta.get('score', 0):
                sector_meta = new_sector_meta
            return sector_meta

        for sector in self.sectors:
            keys = S_KEYS[sector]
            if self.sector_meta.get(sector):
                continue
            sector_meta = {}
            for key in keys:
                sector_meta = search(key, sector_meta)
            if sector_meta.get('score') > 90:
                self.sector_meta[sector] = sector_meta

    def post_processing(self):
        for sector, option in self.sector_meta.items():
            text = option['text']
            sector_score = option['score']
            if not self.field_meta.get(sector):
                self.field_meta[sector] = {}
            for field in SF_KEYS:
                for field_key in SF_KEYS[field]:
                    search = re.search(field_key, text, re.IGNORECASE)
                    if search:
                        start, end = search.span()
                        if not self.field_meta.get(sector).get(field):
                            self.field_meta[sector][field] = {
                                'text': text,
                                'start_index': start,
                                'end_index': end,
                                'score': 100,
                                'sector_score': sector_score,
                            }
                        break
                if not self.field_meta.get(sector, {}).get(field):
                    ratio = 0
                    field_meta = {}
                    for field_key in SF_KEYS[field]:
                        search_text = field_key.split()
                        search_text_n = len(search_text)
                        texts = text.split()
                        for index in range(0, len(texts) - search_text_n):
                            real_text = texts[index:index+search_text_n]
                            new_ratio = fuzz.partial_ratio(real_text, search_text)
                            if not new_ratio > ratio:
                                continue
                            try:
                                search = re.search(' '.join(real_text), text)
                                if search:
                                    start, end = search.span()
                                    ratio = new_ratio
                                    field_meta = {
                                        'text': text,
                                        'start_index': start,
                                        'end_index': end,
                                        'score': new_ratio,
                                        'sector_score': sector_score,
                                    }
                            except re.error:
                                pass
                    if field_meta.get('score'):
                        self.field_meta[sector][field] = field_meta

    def extract(self):
        for sector, fields in self.field_meta.items():
            for field, option in fields.items():
                near_end_index = 10000
                end_index = option['end_index']
                for _field, _option in fields.items():
                    field_start_index = _option['start_index']
                    if (field_start_index > end_index) and\
                            (field_start_index < near_end_index):
                        near_end_index = field_start_index
                    text_block = option['text'][:near_end_index]
                text = text_block[end_index:].strip()
                if not self.extracted.get(sector):
                    self.extracted[sector] = {}
                if not self.extracted.get(sector).get(field):
                    self.extracted[sector][field] = {
                        'value': text,
                        'score': '{} {}'.format(
                            option['sector_score']/100, option['score']/100
                        )
                    }

    def get_extracted_without_score(self):
        extracted = {}
        for sector in self.extracted.keys():
            extracted[sector] = {}
            for field in self.extracted[sector].keys():
                extracted[sector][field] = self.extracted[sector][field]['value']
        return extracted

    def extract_fields(self):
        self.pre_processing()
        self.fuzzy_find_remainig_sectors()
        self.post_processing()
        self.extract()
        return self.extracted, self.get_extracted_without_score()
