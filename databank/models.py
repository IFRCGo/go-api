from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import JSONField

from django.db import models

from api.models import Country, Appeal


class Status:
    ACTIVE = 'active'
    NOT_ACTIVE = 'not_active'

    CHOICES = (
        (ACTIVE, _('Active')),
        (NOT_ACTIVE, _('Not Active')),
    )


class Month:
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

    CHOICES = (
        (JANUARY, _('January')),
        (FEBRUARY, _('February')),
        (MARCH, _('March')),
        (APRIL, _('April')),
        (MAY, _('May')),
        (JUNE, _('June')),
        (JULY, _('July')),
        (AUGUST, _('August')),
        (SEPTEMBER, _('September')),
        (OCTOBER, _('October')),
        (NOVEMBER, _('November')),
        (DECEMBER, _('December')),
    )
    LABEL_MAP = {
        value: label
        for value, label in CHOICES
    }


class PastCrisesEvent():
    COLD_WAVE = 'CW'
    HEAT_WAVE = 'HT'
    DROUGHT = 'DR'
    EARTHQUAKE = 'EQ'
    LAND_SLIDE = 'LS'
    TSUNAMI = 'TS'
    VOLCANO = 'VO'
    EXTRATROPICAL_CYCLONE = 'EC'
    TROPICAL_CYCLONE = 'TC'
    STORM_SURGE = 'SS'
    FLOOD = 'FL'
    FLASH_FLOOD = 'FF'
    COMPLEX_EMERGENCY = 'CE'
    FIRE = 'FR'
    OTHER = 'OT'

    CHOICES = (
        (COLD_WAVE, _('Cold Wave')),
        (HEAT_WAVE, _('Heat Wave')),
        (DROUGHT, _('Drought')),
        (EARTHQUAKE, _('Earthquake')),
        (LAND_SLIDE, _('Land Slide')),
        (TSUNAMI, _('Tsunami')),
        (VOLCANO, _('Volcano')),
        (EXTRATROPICAL_CYCLONE, _('Extratropical Cyclone')),
        (TROPICAL_CYCLONE, _('Tropical Cyclone')),
        (STORM_SURGE, _('Storm Surge')),
        (FLOOD, _('Flood')),
        (FLASH_FLOOD, _('Flash Flood')),
        (COMPLEX_EMERGENCY, _('Complex Emergency')),
        (FIRE, _('Fire')),
        (OTHER, _('Other')),
    )
    LABEL_MAP = {
        value: label
        for value, label in CHOICES
    }


class PastEpidemic():
    # Value are used to search in Reliefweb
    CHOLERA = 'cholera'
    MENINGITIS = 'meningitis'
    RIFT_VALLEY_FEVER = 'rift valley fever'
    HAEMORRHAGIC_FEVERS = 'haemorrhagic fevers'
    HEPATITIS = 'hepatitis'
    YELLOW_FEVER = 'yellow fever'

    CHOICES = (
        (CHOLERA, _('Cholera Outbreak')),
        (MENINGITIS, _('Meningitis')),
        (RIFT_VALLEY_FEVER, _('Rift Valley fever')),
        (HAEMORRHAGIC_FEVERS, _('Viral haemorrhagic fevers')),
        (HEPATITIS, _('Viral hepatitis')),
        (YELLOW_FEVER, _('Yellow fever')),
    )
    LABEL_MAP = {
        value: label
        for value, label in CHOICES
    }


class InformIndicator():
    # Grouping indicators
    GROUP_LABELS = {
        'HA': _('Hazard & Exposure'),
        'VU': _('Vulnerability'),
        'CC': _('Lack Of Coping Capacity'),
    }

    # Indicators
    CHOICES = (
        ('HDI-Est', _('Estimated HDI from GDP per capita')),
        ('INFORM', _('INFORM Risk Index')),
        ('HA', _('Hazard & Exposure Index')),
        ('VU', _('Vulnerability Index')),
        ('CC', _('Lack of Coping Capacity Index')),

        # HAZARD AND EXPOSURE
        ('HA.HUM', _('Human Hazard')),
        ('HA.HUM.CON', _('Current conflicts')),
        ('HA.HUM.CON.GCRI', _('GCRI Internal conflicts')),
        ('HA.HUM.CON.HVC', _('Highly Violent Conflict probability Score')),
        ('HA.HUM.CON.VC', _('Violent Conflict probability Score')),
        ('HA.NAT', _('Natural Hazard')),
        ('HA.NAT.DR', _('Droughts probability and historical impact')),
        ('HA.NAT.DR.AFF', _('People affected by droughts')),
        ('HA.NAT.DR.AFF-FREQ', _('People affected by drought and Frequency of events')),
        ('HA.NAT.DR.ASI', _('Agriculture Drought Probability')),
        ('HA.NAT.DR.ASI_temp', _('Agriculture Drought Probability')),
        ('HA.NAT.DR.FREQ', _('Frequency of drought events')),
        ('HA.NAT.EPI', _('Epidemic')),
        ('HA.NAT.EQ', _('Physical exposure to earthquakes')),
        ('HA.NAT.FL', _('Physical exposure to floods')),
        ('HA.NAT.TC', _('Physical exposure to tropical cyclones')),
        ('HA.NAT.TS', _('Physical exposure to tsunamis')),

        # VULNERABILITY
        ('VU.SEV', _('Socio-Economic Vulnerability')),
        ('VU.SEV.AD', _('Economic Dependency')),
        ('VU.SEV.INQ', _('Inequality')),
        ('VU.SEV.INQ.GII', _('Gender Inequality Index')),
        ('VU.SEV.INQ.GINI', _('Income Gini coefficient')),
        ('VU.SEV.PD', _('Poverty & Development')),
        ('VU.SEV.PD.HDI', _('Human Development Index')),
        ('VU.SEV.PD.MPI', _('Multidimensional Poverty Index')),
        ('VU.VGR', _('Vulnerable Groups')),
        ('VU.VGR.OG', _('Others Vulnerable Groups')),
        ('VU.VGR.UP', _('Uprooted people')),

        # LACK OF COPING CAPACITY
        ('CC.INF.AHC', _('Access to Health Care')),
        ('CC.INF.COM', _('Communication')),
        ('CC.INF.PHY', _('Physical Infrastructure')),
        ('CC.INS.DRR', _('Disaster Risk Reduction')),
        ('CC.INS.GOV', _('Governance')),
    )
    LABEL_MAP = {
        value: label
        for value, label in CHOICES
    }

    @classmethod
    def get_group(cls, indicator):
        if isinstance(indicator, str) and indicator.find('.') != -1:
            return indicator.split('.')[0]

    @classmethod
    def get_group_display(cls, indicator):
        return str(cls.GROUP_LABELS.get(cls.get_group(indicator)))


class CountryOverview(models.Model):
    country = models.OneToOneField(Country, on_delete=models.CASCADE, primary_key=True)
    script_modified_at = models.DateTimeField(null=True, blank=True)

    # Country Key Indicators (Using Script: FDRS API)
    population = models.IntegerField(null=True, blank=True, verbose_name=_('population'))
    gdp = models.FloatField(verbose_name=_('GDP'), null=True, blank=True)
    gnipc = models.IntegerField(verbose_name=_('GNI/CAPITA'), null=True, blank=True)
    life_expectancy = models.IntegerField(null=True, blank=True, verbose_name=_('life expectancy'))
    urban_population = models.FloatField(
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        verbose_name=_('urban POP (%)'),
        null=True, blank=True,
    )
    poverty = models.FloatField(
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        verbose_name=_('poverty (%)'),
        null=True, blank=True,
    )
    literacy = models.FloatField(
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        verbose_name=_('literacy (%)'),
        null=True, blank=True,
    )

    # National Society Indicators (Using Script: FDRS API)
    income = models.FloatField(verbose_name=_('income (CHF)'), null=True, blank=True)
    expenditures = models.FloatField(verbose_name=_('expenditures (CHF)'), null=True, blank=True)
    volunteers = models.IntegerField(verbose_name=_('volunteers'), null=True, blank=True)
    trained_in_first_aid = models.IntegerField(verbose_name=_('trained in first aid'), null=True, blank=True)

    # Key Climate Event (Manual Entry)
    avg_temperature = models.FloatField(verbose_name=_('average temperature'), null=True, blank=True)
    avg_rainfall_precipitation = models.FloatField(verbose_name=_('average rainfall precipitation'), null=True, blank=True)
    rainy_season = models.CharField(verbose_name=_('rainy season'), choices=Status.CHOICES, max_length=20, blank=True, null=True)

    # JSON DATA (Using Script)
    # TODO: Seperate this to multiple tables to support Translation (not required for fts_data)
    fts_data = JSONField(verbose_name=_('FTS data'), default=list)
    start_network_data = JSONField(verbose_name=_('start network data'), default=list)
    past_crises_events = JSONField(verbose_name=_('past crises data'), default=list)
    past_epidemics = JSONField(verbose_name=_('past epidemics data'), default=list)
    inform_indicators = JSONField(verbose_name=_('inform indicators data'), default=list)

    class Meta:
        verbose_name = _('country overview')
        verbose_name_plural = _('countries overview')

    def __str__(self):
        return str(self.country)

    @property
    def appeals(self):
        return Appeal.objects.filter(country=self.country).all()

    @property
    def past_crises_events_count(self):
        return self.pastcrisesevent_set.count()


class SocialEvent(models.Model):
    overview = models.ForeignKey(CountryOverview, verbose_name=_('country overview'), on_delete=models.CASCADE)
    label = models.CharField(verbose_name=_('label'), max_length=255)
    value = models.CharField(verbose_name=_('value'), max_length=255)

    class Meta:
        unique_together = ('overview', 'label')
        verbose_name = _('Social Event')
        verbose_name_plural = _('Social Events')

    def __str__(self):
        return f'{self.overview} - {self.label}: {self.value}'


class KeyClimateEvent(models.Model):
    overview = models.ForeignKey(CountryOverview, verbose_name=_('country overview'), on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_('modified at'))

    month = models.PositiveSmallIntegerField(choices=Month.CHOICES, verbose_name=_('month'))
    # TODO: Add validation min < max
    avg_max_temperature = models.FloatField(verbose_name=_('average maximum temperature'))
    avg_min_temperature = models.FloatField(verbose_name=_('average minimum temperature'))
    avg_rainfall_precipitation = models.FloatField(verbose_name=_('average rainfall precipitation'))

    class Meta:
        unique_together = ('overview', 'month')
        verbose_name = _('Key Client Event')
        verbose_name_plural = _('Key Client Events')

    def __str__(self):
        return f'{self.overview.country} - {self.get_month_display()}'


class SeasonalCalender(models.Model):
    overview = models.ForeignKey(CountryOverview, on_delete=models.CASCADE, verbose_name=_('country overview'))
    modified_at = models.DateTimeField(auto_now=True, verbose_name=_('modified at'))
    title = models.CharField(max_length=20, verbose_name=_('title'))  # TODO: CHOICES?
    sector = models.CharField(max_length=20, verbose_name=_('sector'))  # TODO: CHOICES?
    date_start = models.DateField(verbose_name=_('date start'))
    date_end = models.DateField(verbose_name=_('date end'))

    class Meta:
        unique_together = ('overview', 'sector', 'title')
        verbose_name = _('Seasonal Calender Record')
        verbose_name_plural = _('Seasonal Calender Records')

    def __str__(self):
        return f'{self.overview.country} - {self.title} - {self.sector}'


class KeyDocumentGroup(models.Model):
    title = models.CharField(max_length=20, verbose_name=_('title'))

    def __str__(self):
        return self.title


def key_document_path(instance, filename):
    return 'country-key-documents/%s/%s' % (instance.overview.country_id, filename)


class KeyDocument(models.Model):
    overview = models.ForeignKey(CountryOverview, verbose_name=_('country overview'), on_delete=models.CASCADE)
    title = models.CharField(max_length=20, verbose_name=_('title'))
    group = models.ForeignKey(KeyDocumentGroup, on_delete=models.CASCADE, verbose_name=_('group'))
    date = models.DateField(verbose_name=_('date'))
    file = models.FileField(verbose_name=_('file'), upload_to=key_document_path)

    def __str__(self):
        return f'{self.title}, {self.date}'


class ExternalSource(models.Model):
    overview = models.ForeignKey(CountryOverview, verbose_name=_('country overview'), on_delete=models.CASCADE)
    title = models.CharField(max_length=20, verbose_name=_('title'))
    url = models.URLField(verbose_name=_('url'), max_length=300)

    def __str__(self):
        return f'{self.title}: {self.url}'
