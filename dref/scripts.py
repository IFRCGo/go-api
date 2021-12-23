import os

from pdf2image import convert_from_path


def pdf_image_extractor(file):
    pages = convert_from_path(file)
    for i in range(len(pages)):
        page = pages[i]
        page.save(f'{file}_preview.png', 'PNG')
        with open(f'{file}_preview.png') as f:
            _, tail = os.path.split(f.name)
            return os.path.join('dref/images', tail)
