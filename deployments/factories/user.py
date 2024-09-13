import factory
from django.contrib.auth import get_user_model

from api.models import Profile


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: "user_%d" % n)
    email = factory.Sequence(lambda n: "user_%d@ifrc.org" % n)

    @factory.post_generation
    def create_profile(obj, create, extracted, **kwargs):
        if create:
            profile = Profile.objects.get(user=obj)
            profile.limit_access_to_guest = False
            profile.save(update_fields=["limit_access_to_guest"])
            # Set new profile to the user object
            obj.profile = profile
