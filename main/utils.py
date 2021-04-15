from collections import defaultdict


def is_tableau(request):
    """ Checking the request for the 'tableau' parameter
        (used mostly for switching to the *TableauSerializers)
    """
    return request.GET.get('tableau', 'false').lower() == 'true'


def get_merged_items_by_fields(items, fields, seperator=', '):
    """
    For given array and fields:
    input: [{'name': 'name 1', 'age': 2}, {'name': 'name 2', 'height': 32}], ['name', 'age']
    output: {'name': 'name 1, name 2', 'age': '2'}
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
