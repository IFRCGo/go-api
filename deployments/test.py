from django.test import TestCase
import deployments.models as models


class ERUOwnerTest(TestCase):

    def setUp(self):
        country = models.Country.objects.create(name='country')
        eru_owner = models.ERUOwner.objects.create(pk=1, country=country)
        eru = models.ERU.objects.create(type=2, units=6, eru_owner=eru_owner)

    def test_eru_owner_create(self):
        eru_owner = models.ERUOwner.objects.get(pk=1)
        country = models.Country.objects.get(name='country')
        self.assertEqual(eru_owner.country, country)
        erus = eru_owner.eru_set.all()
        self.assertEqual(erus.count(), 1)
        self.assertEqual(erus[0].type, 2)
        self.assertEqual(erus[0].units, 6)

