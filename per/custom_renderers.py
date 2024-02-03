from rest_framework_csv.renderers import PaginatedCSVRenderer
from main.settings import SEP
from collections import OrderedDict


class NarrowCSVRenderer(PaginatedCSVRenderer):

    def render(self, data, *args, **kwargs):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
            if args[1]['view'].basename == 'ops_learning' and data and 'sector' in data[0]:
                data2 = []
                for i, d in enumerate(data):
                    for orgn in d['organization'].split(SEP):
                        for sect in d['sector'].split(SEP):
                            for pcom in d['per_component'].split(SEP):
                                row = OrderedDict()
                                for k, v in d.items():
                                    if k == 'organization':
                                        row[k] = orgn
                                    elif k == 'sector':
                                        row[k] = sect
                                    elif k == 'per_component':
                                        row[k] = pcom
                                    else:
                                        row[k] = v
                                data2.append(row)
                return super(PaginatedCSVRenderer, self).render(data2, *args, **kwargs)

        return super(PaginatedCSVRenderer, self).render(data, *args, **kwargs)
