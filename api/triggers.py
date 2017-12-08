import os
from django.db.models.signals import post_save
from django.template import loader
from django.forms.models import model_to_dict
from django.contrib.auth.models import User

from .esconnection import ES_CLIENT
from .models import Profile, Event, Appeal, FieldReport
from notifications.models import Subscription, SubscriptionType, RecordType


# Save a user profile whenever we create a user
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

post_save.connect(create_profile, sender=User)


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
    '%s%s' % (RecordType.EVENT, SubscriptionType.NEW) : 'email/new_event.html',
    '%s%s' % (RecordType.EVENT, SubscriptionType.EDIT) : 'email/new_event.html',
    '%s%s' % (RecordType.APPEAL, SubscriptionType.NEW) : 'email/new_appeal.html',
    '%s%s' % (RecordType.APPEAL, SubscriptionType.EDIT) : 'email/new_appeal.html',
    '%s%s' % (RecordType.FIELD_REPORT, SubscriptionType.NEW) : 'email/new_report.html',
    '%s%s' % (RecordType.FIELD_REPORT, SubscriptionType.EDIT) : 'email/new_report.html',
}


def send_notification(sender, instance, created, **kwargs):
    rtype = getattr(RecordType, instance.record_type())
    stype = SubscriptionType.NEW if created else SubscriptionType.EDIT

    subscribers = User.objects.filter(subscription__rtype=rtype, subscription__stype=stype).values('email')

    context = model_to_dict(instance)
    print(context)

    template_path = template_paths['%s%s' % (rtype, stype)]
    template = loader.get_template(template_path)
    content = template.render(context=context)
    print(content)

if os.environ.get('BULK_IMPORT') != '1':
    post_save.connect(send_notification, sender=Event)
