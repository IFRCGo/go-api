import os
from django.db import transaction
from django.db.models.signals import post_save, m2m_changed
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.db.models.fields.related import ManyToManyField
from django.conf import settings

from .esconnection import ES_CLIENT
from .models import Profile, Event, Appeal, FieldReport, Country
from notifications.models import Subscription, SubscriptionType, RecordType
from notifications.notification import send_notification


# Save a user profile whenever we create a user
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
post_save.connect(create_profile, sender=User)


def save_fieldreport_region(sender, instance, action, **kwargs):
    if (action == 'post_add' or action == 'post_remove'):
        countries = Country.objects.select_related().filter(fieldreport=instance)
        for country in countries:
            if country.region is not None:
                instance.regions.add(country.region)
m2m_changed.connect(save_fieldreport_region, sender=FieldReport.countries.through)


def index_es(sender, instance, created, **kwargs):
    def on_commit():
        if ES_CLIENT is not None:
            ES_CLIENT.index(
                index=instance.es_index(),
                doc_type='page',
                id=instance.es_id(),
                body=instance.indexing(),
            )
    transaction.on_commit(on_commit)

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


def notify(sender, instance, created, **kwargs):
    def on_commit():
        record_type = instance.record_type()
        rtype = getattr(RecordType, record_type)
        stype = SubscriptionType.NEW if created else SubscriptionType.EDIT

        subscribers = User.objects.filter(subscription__rtype=rtype, subscription__stype=stype).values('email')

        lookups = []
        # add subscribers who have subscribed to this specific disaster type
        if instance.dtype is not None:
            lookups.append('d%s' % instance.dtype.id)

        # appeals have one country, events and reports have multiple
        # also include attached regions
        if record_type == 'APPEAL' and instance.country is not None:
            lookups.append('c%s' % instance.country.id)
            if instance.country.region is not None:
                lookups.append('%rs' % instance.country.region.id)
        elif instance.countries is not None:
            countries = instance.countries.prefetch_related('region').all()
            lookups += ['c%s' % country.id for country in countries]
            lookups += ['r%s' % getattr(country, 'region.id', None) for country in countries]

        if len(lookups):
            subscribers = (subscribers | User.objects.filter(subscription__lookup_id__in=lookups).values('email')).distinct()

        if len(subscribers):
            context = instance.to_dict()
            context['resource_uri'] = '%s/%s/%s/' % (settings.BASE_URL, record_type.lower(), instance.id)
            context['admin_uri'] = '%s/%s/' % (settings.BASE_URL, 'admin')
            if instance.dtype is not None:
                context['dtype'] = instance.dtype.name

            template_path = template_paths['%s%s' % (rtype, stype)]
            html = render_to_string(template_path, context)
            recipients = [s['email'] for s in subscribers]

            adj = 'New' if created else 'Modified'
            subject = '%s %s in IFRC GO' % (adj, record_type.lower())

            send_notification(subject, recipients, html)

    transaction.on_commit(on_commit)

if os.environ.get('BULK_IMPORT') != '1':
    post_save.connect(notify, sender=Event)
    post_save.connect(notify, sender=Appeal)
    post_save.connect(notify, sender=FieldReport)
