from django.db import models


class DisasterType(models.Model):
    """ Type of disaster """
    name = models.CharField(max_length=100)
    summary = models.TextField()

    def __str__(self):
        return self.name


class Event(models.Model):
    """ A disaster, which could cover multiple countries """

    name = models.CharField(max_length=100)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # type = models.ForeignKey(DisasterType)

    def countries(self):
        """ Get countries from all appeals and field reports in this disaster """
        #countries1 = [appeal.country for appeal in self.appeal_set.all()]
        countries = [country for fr in self.fieldreport_set.all() for country in fr.countries.all()]
        #flat_list = [item for sublist in l for item in sublist]

        #countries2 = [fr.country for fr in self.fieldreport_set.all()]
        return list(set([c.name for c in countries]))

    def __str__(self):
        return self.name


class Country(models.Model):
    """ A country """

    name = models.CharField(max_length=100)
    iso = models.CharField(max_length=2, null=True)
    society_name = models.TextField(default="")

    def __str__(self):
        return self.name


class Document(models.Model):
    """ A document, located somwehere """

    name = models.CharField(max_length=100)
    uri = models.TextField()

    def __str__(self):
        return self.name


class Appeal(models.Model):
    """ An appeal for a disaster and country, containing documents """

    # appeal ID, assinged by creator
    aid = models.CharField(max_length=100)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    #disaster = models.ForeignKey(Event, null=True)
    #country = models.ForeignKey(Country)
    #documents = models.ManyToManyField(Document)

    def __str__(self):
        return self.aid


class FieldReport(models.Model):
    """ A field report for a disaster and country, containing documents """

    rid = models.CharField(max_length=100)
    summary = models.TextField(blank=True)
    description = models.TextField(blank=True, default='')
    dtype = models.ForeignKey(DisasterType)
    event = models.ForeignKey(Event, null=True)
    countries = models.ManyToManyField(Country)
    status = models.IntegerField(default=0)
    request_assistance = models.BooleanField(default=False)

    num_injured = models.IntegerField(null=True)
    num_dead = models.IntegerField(null=True)
    num_missing = models.IntegerField(null=True)
    num_affected = models.IntegerField(null=True)
    num_displaced = models.IntegerField(null=True)
    num_assisted_gov = models.IntegerField(null=True)
    num_assisted_rc = models.IntegerField(null=True)
    num_localstaff = models.IntegerField(null=True)
    num_volunteers = models.IntegerField(null=True)
    num_expats_delegates = models.IntegerField(null=True)

    # action IDs - other tables?
    action = models.TextField(blank=True, default='')

    # contacts

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.aid


class Service(models.Model):
    """ A resource that may or may not be deployed """

    name = models.CharField(max_length=100)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    deployed = models.BooleanField(default=False)
    location = models.TextField()

    def __str__(self):
        return self.name
