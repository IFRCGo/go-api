from django.db import models
from django.db.models import Q
from rest_framework import viewsets, request

from deployments.models import Project
from .models import VisibilityChoices, VisibilityCharChoices, UserCountry, Profile
from .utils import is_user_ifrc  # filter_visibility_by_auth (would be better)

from api.models import FieldReport, Event
from api.utils import get_user_countries
from .utils import is_user_ifrc


class ReadOnlyVisibilityViewsetMixin():
    request: request.Request

    def get_visibility_queryset(self, queryset):
        choices = VisibilityChoices

        # TODO: Use VisibilityChoices (ENUM) on projects as well [Refactor]
        if queryset.model == Project:
            choices = VisibilityCharChoices

        if not self.request.user.is_authenticated:
            return queryset.filter(visibility=choices.PUBLIC)
        if is_user_ifrc(self.request.user):  # IFRC ADMIN or Superuser
            return queryset
        queryset = queryset.exclude(visibility=choices.IFRC)
        # For specific models
        if queryset.model in [FieldReport, Event]:
            user_countries_qs = get_user_countries(self.request.user)
            return queryset\
                .exclude(
                    models.Q(visibility=VisibilityChoices.IFRC_NS) &
                    # This depends on the model
                    ~models.Q(countries__id__in=user_countries_qs)
                )
        # For generic models try to use get_for is available
        if hasattr(queryset.model, 'get_for'):
            return queryset.model.get_for(self.request.user, queryset=queryset)
        return queryset

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
                if self.visibility_model_class.__name__ == "FieldReport" or self.visibility_model_class.__name__ == "Event":
                    return self.visibility_model_class.objects.exclude(visibility=VisibilityChoices.IFRC).exclude(
                        Q(visibility=VisibilityChoices.IFRC_NS)
                        & ~Q(
                            countries__id__in=UserCountry.objects.filter(user=self.request.user.id)
                            .values_list("country", flat=True)
                            .union(Profile.objects.filter(user=self.request.user.id).values_list("country", flat=True))
                        )
                    )
                else:
                    return self.visibility_model_class.objects.exclude(visibility=VisibilityChoices.IFRC)

        return self.visibility_model_class.objects.filter(visibility=VisibilityChoices.PUBLIC)
