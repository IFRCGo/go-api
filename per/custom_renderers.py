from rest_framework_csv.renderers import PaginatedCSVRenderer
from main.settings import SEP
from collections import OrderedDict


class NarrowCSVRenderer(PaginatedCSVRenderer):
    """
    The aim of this custom renderer: to avoid flattening of multiple values.
    (Flattening means: displaying lists as value.0, value.1, value.2)
    Instead of this we would like to show these in different rows.
    Maybe there is an easier way also to achieve this.
    See also: admin.py::export_selected_records()
    """

    def render(self, data, *args, **kwargs):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
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
