from collections import defaultdict

from rest_framework.renderers import BrowsableAPIRenderer


def is_tableau(request):
    """ Checking the request for the 'tableau' parameter
        (used mostly for switching to the *TableauSerializers)
    """
    return request.GET.get('tableau', 'false').lower() == 'true'


def get_merged_items_by_fields(items, fields, seperator=', '):
    """
    For given array and fields:
    input: [{'name': 'name 1', 'age': 2}, {'name': 'name 2', 'height': 32}], ['name', 'age']
    output: {'name': 'name 1, name 2', 'age': '2, '}
    """
    data = defaultdict(list)
    for item in items:
        for field in fields:
            value = getattr(item, field, None)
            if value is not None:
                data[field].append(str(value))
    return {
        field: seperator.join(data[field])
        for field in fields
    }


class BrowsableAPIRendererWithRawForms(BrowsableAPIRenderer):  # It is done to reduce load time in browsable api.
    """
    Renders the browsable api, but excludes the normal forms.
    Only show raw form.
    """

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        ctx['post_form'] = None
        return ctx

    def get_rendered_html_form(self, data, view, method, request):
        """Why render _any_ forms at all. This method should return
        rendered HTML, so let's simply return an empty string.
        """
        return ""
