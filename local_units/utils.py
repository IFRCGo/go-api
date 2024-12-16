from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def get_email_context(instance):
    from local_units.serializers import PrivateLocalUnitDetailSerializer

    local_unit_data = PrivateLocalUnitDetailSerializer(instance).data
    email_context = {
        "id": local_unit_data["id"],
        "frontend_url": settings.FRONTEND_URL,
    }
    return email_context


def get_local_admins(instance):

    local_admins = User.objects.filter(local_units=instance, role="local_admin")
    return local_admins.values_list("email", flat=True)
