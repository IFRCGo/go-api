from rest_framework import viewsets

from deployments.models import Project
from .models import VisibilityChoices, VisibilityCharChoices
from .utils import is_user_ifrc  # filter_visibility_by_auth (would be better)


class ReadOnlyVisibilityViewsetMixin():
    def get_visibility_queryset(self, queryset):
        choices = VisibilityChoices

        # TODO: Use VisibilityChoices (ENUM) on projects as well [Refactor]
        if queryset.model == Project:
            choices = VisibilityCharChoices

        if self.request.user.is_authenticated:
            if is_user_ifrc(self.request.user):
                return queryset
            else:
                return queryset.exclude(visibility=choices.IFRC)
        return queryset.filter(visibility=choices.PUBLIC)

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.get_visibility_queryset(queryset)


# TODO: Use ReadOnlyVisibilityViewsetMixin instead of ReadOnlyVisibilityViewset
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
