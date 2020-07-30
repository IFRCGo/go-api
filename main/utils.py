def is_tableau(request):
    """ Checking the request for the 'tableau' parameter
        (used mostly for switching to the *TableauSerializers)
    """
    return request.GET.get('tableau', 'false').lower() == 'true'
