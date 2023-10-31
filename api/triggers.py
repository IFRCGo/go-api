from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .models import Profile


# Save a user profile whenever we create a user
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


post_save.connect(create_profile, sender=User)
