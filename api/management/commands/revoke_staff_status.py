import requests
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.logger import logger
#from registrations.views import is_valid_domain

class Command(BaseCommand):
    help = 'Update staff status in auth_user table according to "Read only" group'

    def get_readonly_users(self):
        readonly = []
        for u in User.objects.filter(is_staff=True).filter(is_superuser=False):
            if u.groups.filter(name__icontains='read only'):
                readonly.append(u)
                logger.info("Read only: " + u.get_full_name())
        
        return readonly

#   def get_editor_users(self):
#       editors = []
#       #import pdb; pdb.set_trace()
#       for u in User.objects.filter(is_staff=False).filter(is_superuser=False):
#           if is_valid_domain(u.email) and not u.groups.filter(name__icontains='read only'):
#                editors.append(u)
#                print ("Editor again: " + u.get_full_name())
#                # Prints a lots of users
#       
#       return editors

    def handle(self, *args, **options):
        logger.info('Moving Read only users out of staff status...')
        users = self.get_readonly_users()
        if len(users) > 0:
            logger.info('Revoking staff status from %s user%s' % (len(users), 's' if len(users) > 1 else ''))
            num_updated = 0
            for u in users:
                u.is_staff = False
                try:
                    u.save()
                except Exception as e:
                    logger.error(str(e)[:100])
                    logger.error('Could not update user %s' % u.email)
                    continue
                num_updated = num_updated + 1
                logger.info(' %s user%s updated' % (num_updated, 's' if num_updated > 1 else ''))
            logger.info('... user%s moving completed' % ('s' if len(users) > 1 else ''))

        else:
            logger.info('... not found any users to be moved')
