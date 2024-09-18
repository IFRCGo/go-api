from django.utils.functional import cached_property

from api.dataloaders import ApiDataLoader


# TODO: Use optimizer instead?
class GlobalDataLoader:

    @cached_property
    def api(self):
        return ApiDataLoader()
