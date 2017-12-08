import os
from django.db.models.signals import post_save
from django.conf import settings

from .esconnection import ES_CLIENT
from .models import Profile, Event, Appeal, FieldReport


# Save a user profile whenever we create a user
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
post_save.connect(create_profile, sender=settings.AUTH_USER_MODEL)


def index_es(sender, instance, created, **kwargs):
    if ES_CLIENT is not None:
        ES_CLIENT.index(
            index=instance.es_index(),
            doc_type='page',
            id=instance.es_id(),
            body=instance.indexing(),
        )


# Avoid automatic indexing during bulk imports
if os.environ.get('BULK_IMPORT') != '1' and ES_CLIENT is not None:
    post_save.connect(index_es, sender=Event)
    post_save.connect(index_es, sender=Appeal)
    post_save.connect(index_es, sender=FieldReport)
