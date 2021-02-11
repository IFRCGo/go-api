from django.core.management.base import BaseCommand
from api.models import MainContact
from django.db import transaction
from api.logger import logger


class Command(BaseCommand):
    help = 'Adds contacts coming from the Resources page into the DB (probably one-time run only)'

    @transaction.atomic
    def handle(self, *args, **options):
        contacts = [
            # Area/field/extent (en, fr, es, ar), name, email
            [
                'Africa Region',
                'Région Afrique',
                'Región de África',
                'منطقة إفريقيا',
                'Elly NANDASABA MULAHA',
                'Elly.MULAHA@ifrc.org'
            ],
            [
                'Americas Region',
                'Région Amériques',
                'Región de América',
                'منطقة الأمريكتين',
                'Luis FANOVICH',
                'luis.fanovich@ifrc.org'
            ],
            [
                'Asia Pacific Region',
                'Région Asie-Pacifique',
                'Región de Asia-Pacífico',
                'منطقة آسيا والمحيط الهادئ',
                'Dedi JUNADI',
                'dedi.junadi@ifrc.org'
            ],
            [
                'Europe Region',
                'Région Europe',
                'Región de Europa',
                'منطقة أوروبا',
                'Anssi ANONEN',
                'anssi.anonen@ifrc.org'
            ],
            [
                'MENA Region',
                'Région MENA',
                'Región de MENA',
                'منطقة الشرق الأوسط وشمال أفريقيا',
                'Ahmad AL JAMAL',
                'ahmad.aljamal@ifrc.org'
            ]
        ]

        error = False
        c_to_add = []
        contacts_empty = not MainContact.objects.exists()

        if contacts_empty:
            for con in contacts:
                contact = MainContact(
                    extent=con[0],
                    extent_en=con[0],
                    extent_fr=con[1],
                    extent_es=con[2],
                    extent_ar=con[3],
                    name=con[4],
                    email=con[5]
                )
                c_to_add.append(contact)

        try:
            MainContact.objects.bulk_create(c_to_add)
        except Exception as ex:
            logger.error(f'Could not create MainContacts. Error: {str(ex)}')
            error = True

        if not error:
            logger.info('Successfully added MainContacts.')
