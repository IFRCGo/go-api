import os
from django.db.models.signals import post_save
from django.conf import settings
from django.template import loader
from django.forms.models import model_to_dict

from .esconnection import ES_CLIENT
from .models import Profile, Event, Appeal, FieldReport
from notifications.models import Subscription, SubscriptionType, RecordType


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


template_paths = {
    '%s%s' % (RecordType.EVENT, SubscriptionType.NEW) : 'email/new_appeal.html',
    '%s%s' % (RecordType.EVENT, SubscriptionType.EDIT) : 'email/new_appeal.html',
}


def send_email(sender, instance, created, **kwargs):
    print('in event post save')
    rtype = getattr(RecordType, instance.record_type())
    stype = SubscriptionType.NEW if created else SubscriptionType.EDIT
    print(rtype, stype)

    subscribers = Subscription.objects.filter(rtype=rtype, stype=stype).values('user')
    print(subscribers)

    context = model_to_dict(instance)
    print(context)

    template_path = template_paths['%s%s' % (rtype, stype)]
    print(template_path)
    template = loader.get_template(template_path)
    content = template.render(context=context)
    print(content)

if os.environ.get('BULK_IMPORT') != '1':
    post_save.connect(send_email, sender=Event)
