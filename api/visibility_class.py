from rest_framework import viewsets
from .models import VisibilityChoices
from .utils import is_user_ifrc # filter_visibility_by_auth (would be better)

class ReadOnlyVisibilityViewset(viewsets.ReadOnlyModelViewSet):
    visibility_model_class = None

    def get_queryset(self):
        # FIXME: utils.py:43
        # filter_visibility_by_auth(user=self.request.user, visibility_model_class=self.visibility_model_class)
        if self.request.user.is_authenticated:
            if is_user_ifrc(self.request.user):
                return self.visibility_model_class.objects.all()
            else:
                return self.visibility_model_class.objects.exclude(visibility=VisibilityChoices.IFRC)
        return self.visibility_model_class.objects.filter(visibility=VisibilityChoices.PUBLIC)
