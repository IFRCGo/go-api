import re
from fuzzywuzzy import fuzz
from config import (
    M_KEYS,
    M_EXTRACTORS,
    get_meta_misc_keys,
    # get_sector_misc_keys,
)


class MetaFieldExtractor():
    def __init__(self, texts, fields):
        self.texts = texts
        self.fields = fields
        self.misc_fields = get_meta_misc_keys(fields)
        self.text_meta = {}
        self.field_meta = {}
        self.extracted = {}

    def find_block_for_key(self, text, index, field=None, misc=False):
        fields = M_KEYS[field] if not misc else self.misc_fields
        for key in fields:
            search = re.search(key, text, re.IGNORECASE)
            if search:
                start, end = search.span()
                if misc:
                    _field = '{}_misc'.format(key)
                else:
                    _field = field
                if self.field_meta.get(_field):
                    continue
                self.field_meta[_field] = {
                    'text_index': index,
                    'text': text,
                    'start_index': start,
                    'end_index': end,
                    'score': 100,
                }
                if not self.text_meta.get(index):
                    self.text_meta[index] = []
                self.text_meta[index].append(_field)
                if not misc:
                    break

    def fuzzy_find_remainig_key(self):
        def _search(key):
            ratio = 0
            field_meta = {}
            for text_index, text in enumerate(self.texts):
                texts = text.split()
                search_text = key.split()
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
                            field_meta = {
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
            return field_meta

        def search(key, field_meta):
            new_field_meta = _search(key)
            if new_field_meta['score'] > field_meta.get('score', 0):
                field_meta = new_field_meta
            return field_meta

        for field in self.fields:
            keys = M_KEYS[field]
            if self.field_meta.get(field):
                continue
            field_meta = {}
            for key in keys:
                field_meta = search(key, field_meta)
            if field_meta.get('score') > 70:
                self.field_meta[field] = field_meta
                if not self.text_meta.get(field_meta['text_index']):
                    self.text_meta[field_meta['text_index']] = []
                self.text_meta[field_meta['text_index']].append(field)

    def pre_processing(self):
        for index, text in enumerate(self.texts):
            for field in self.fields:
                self.find_block_for_key(text, index, field)
            self.find_block_for_key(text, index, misc=True)
        self.fuzzy_find_remainig_key()

    def text_pre_processing(self, field, meta):
        text_block = meta['text']
        text_index = meta['text_index']
        end_index = meta['end_index']
        if len(self.text_meta[text_index]) > 1:
            near_end_index = 10000
            for field in self.text_meta[text_index]:
                field_start_index = self.field_meta[field]['start_index']
                if (field_start_index > end_index) and\
                        (field_start_index < near_end_index):
                    near_end_index = field_start_index
            text_block = text_block[:near_end_index]
        text = text_block[end_index:].strip()
        return text

    def extract(self):
        for field, meta in self.field_meta.items():
            extractor = M_EXTRACTORS.get(field)
            if extractor:
                self.extracted[field] = {
                    'value': extractor(self.text_pre_processing(field, meta)),
                    'score': meta['score']/100,
                }

    def get_extracted_without_score(self):
        extracted = {}
        for field in self.extracted.keys():
            extracted[field] = self.extracted[field]['value']
        return extracted

    def extract_fields(self):
        self.pre_processing()
        self.extract()
        return self.extracted, self.get_extracted_without_score()
