from django.conf import settings

from dref.models import (
    Dref,
    DrefOperationalUpdate,
    DrefFinalReport,
)
from django.db import models
from django.contrib.postgres.aggregates import ArrayAgg


def get_email_context(instance):
    from dref.serializers import DrefSerializer

    dref_data = DrefSerializer(instance).data
    email_context = {
        'id': dref_data['id'],
        'title': dref_data['title'],
        'frontend_url': settings.FRONTEND_URL,
    }
    return email_context


# get the list fo users in dref
def get_users_in_dref():
    data = Dref.objects.values('id').annotate(created_user_list=ArrayAgg(
        'created_by', filter=models.Q(created_by__isnull=False))
    ).annotate(
        users_list=ArrayAgg('users', filter=models.Q(users__isnull=False))
    ).annotate(
        op_created_by=models.Subquery(
            DrefOperationalUpdate.objects.filter(
                dref=models.OuterRef('id')
            ).order_by().values('id').annotate(
                c=ArrayAgg('created_by', filter=models.Q(created_by__isnull=False))
            ).values('c')[:1]
        ),
        op_users=models.Subquery(
            DrefOperationalUpdate.objects.filter(
                dref=models.OuterRef('id')
            ).order_by().values('id').annotate(
                c=ArrayAgg('users', filter=models.Q(users__isnull=False))
            ).values('c')[:1]
        )
    )
    return data


# get the list fo users in dref
def get_users_in_dref_operational_update():
    data = DrefOperationalUpdate.objects.values('id').annotate(
        created_user_list=ArrayAgg(
            'created_by', filter=models.Q(users__isnull=False)
        ),
        users=ArrayAgg(
            'users', filter=models.Q(users__isnull=False)
        )
    )
    share_with_users = DrefOperationalUpdate.objects.values_list('users', flat=True)
    created_by_users = DrefOperationalUpdate.objects.values_list('created_by', flat=True)
    users = share_with_users.union(created_by_users)
    return users


# get the list fo users in dref
def get_users_in_dref_final_report():
    share_with_users = DrefFinalReport.objects.values_list('users', flat=True)
    created_by_users = DrefFinalReport.objects.values_list('created_by', flat=True)
    users = share_with_users.union(created_by_users)
    return users
