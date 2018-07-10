from rest_framework import viewsets
from .models import VisibilityChoices

class ReadOnlyVisibilityViewset(viewsets.ReadOnlyModelViewSet):
    visibility_model_class = None

    def is_ifrc(self, user):
        if user.has_perm('api.ifrc_admin') or user.is_superuser:
            return True
        return False

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.is_ifrc(self.request.user):
                return self.visibility_model_class.objects.all()
            else:
                return self.visibility_model_class.objects.exclude(visibility=VisibilityChoices.IFRC)
        return self.visibility_model_class.objects.filter(visibility=VisibilityChoices.PUBLIC)
