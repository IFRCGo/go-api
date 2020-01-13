from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.postgres.fields import JSONField

from django.db import models

from api.models import Country, Appeal


class Status:
    ACTIVE = 'active'
    NOT_ACTIVE = 'not_active'

    CHOICES = (
        (ACTIVE, 'Active'),
        (NOT_ACTIVE, 'Not Active'),
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
        (JANUARY, 'January'),
        (FEBRUARY, 'February'),
        (MARCH, 'March'),
        (APRIL, 'April'),
        (MAY, 'May'),
        (JUNE, 'June'),
        (JULY, 'July'),
        (AUGUST, 'August'),
        (SEPTEMBER, 'September'),
        (OCTOBER, 'October'),
        (NOVEMBER, 'November'),
        (DECEMBER, 'December'),
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
        (COLD_WAVE, 'Cold Wave'),
        (HEAT_WAVE, 'Heat Wave'),
        (DROUGHT, 'Drought'),
        (EARTHQUAKE, 'Earthquake'),
        (LAND_SLIDE, 'Land Slide'),
        (TSUNAMI, 'Tsunami'),
        (VOLCANO, 'Volcano'),
        (EXTRATROPICAL_CYCLONE, 'Extratropical Cyclone'),
        (TROPICAL_CYCLONE, 'Tropical Cyclone'),
        (STORM_SURGE, 'Storm Surge'),
        (FLOOD, 'Flood'),
        (FLASH_FLOOD, 'Flash Flood'),
        (COMPLEX_EMERGENCY, 'Complex Emergency'),
        (FIRE, 'Fire'),
        (OTHER, 'Other'),
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
        (CHOLERA, 'Cholera Outbreak'),
        (MENINGITIS, 'Meningitis'),
        (RIFT_VALLEY_FEVER, 'Rift Valley fever'),
        (HAEMORRHAGIC_FEVERS, 'Viral haemorrhagic fevers'),
        (HEPATITIS, 'Viral hepatitis'),
        (YELLOW_FEVER, 'Yellow fever'),
    )
    LABEL_MAP = {
        value: label
        for value, label in CHOICES
    }


class InformIndicator():
    # Grouping indicators
    GROUP_LABELS = {
        'HA': 'Hazard & Exposure',
        'VU': 'Vulnerability',
        'CC': 'Lack Of Coping Capacity',
    }

    # Indicators
    CHOICES = (
        ('HDI-Est', 'Estimated HDI from GDP per capita'),
        ('INFORM', 'INFORM Risk Index'),
        ('HA', 'Hazard & Exposure Index'),
        ('VU', 'Vulnerability Index'),
        ('CC', 'Lack of Coping Capacity Index'),

        # HAZARD AND EXPOSURE
        ('HA.HUM', 'Human Hazard'),
        ('HA.HUM.CON', 'Current conflicts'),
        ('HA.HUM.CON.GCRI', 'GCRI Internal conflicts'),
        ('HA.HUM.CON.HVC', 'Highly Violent Conflict probability Score'),
        ('HA.HUM.CON.VC', 'Violent Conflict probability Score'),
        ('HA.NAT', 'Natural Hazard'),
        ('HA.NAT.DR', 'Droughts probability and historical impact'),
        ('HA.NAT.DR.AFF', 'People affected by droughts'),
        ('HA.NAT.DR.AFF-FREQ', 'People affected by drought and Frequency of events'),
        ('HA.NAT.DR.ASI', 'Agriculture Drought Probability'),
        ('HA.NAT.DR.ASI_temp', 'Agriculture Drought Probability'),
        ('HA.NAT.DR.FREQ', 'Frequency of drought events'),
        ('HA.NAT.EPI', 'Epidemic'),
        ('HA.NAT.EQ', 'Physical exposure to earthquakes'),
        ('HA.NAT.FL', 'Physical exposure to floods'),
        ('HA.NAT.TC', 'Physical exposure to tropical cyclones'),
        ('HA.NAT.TS', 'Physical exposure to tsunamis'),

        # VULNERABILITY
        ('VU.SEV', 'Socio-Economic Vulnerability'),
        ('VU.SEV.AD', 'Economic Dependency'),
        ('VU.SEV.INQ', 'Inequality'),
        ('VU.SEV.INQ.GII', 'Gender Inequality Index'),
        ('VU.SEV.INQ.GINI', 'Income Gini coefficient'),
        ('VU.SEV.PD', 'Poverty & Development'),
        ('VU.SEV.PD.HDI', 'Human Development Index'),
        ('VU.SEV.PD.MPI', 'Multidimensional Poverty Index'),
        ('VU.VGR', 'Vulnerable Groups'),
        ('VU.VGR.OG', 'Others Vulnerable Groups'),
        ('VU.VGR.UP', 'Uprooted people'),

        # LACK OF COPING CAPACITY
        ('CC.INF.AHC', 'Access to Health Care'),
        ('CC.INF.COM', 'Communication'),
        ('CC.INF.PHY', 'Physical Infrastructure'),
        ('CC.INS.DRR', 'Disaster Risk Reduction'),
        ('CC.INS.GOV', 'Governance'),
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
        return cls.GROUP_LABELS.get(cls.get_group(indicator))


class CountryOverview(models.Model):
    country = models.OneToOneField(Country, on_delete=models.CASCADE, primary_key=True)
    script_modified_at = models.DateTimeField(null=True, blank=True)

    # Country Key Indicators (Using Script: FDRS API)
    population = models.IntegerField(null=True, blank=True)
    gdp = models.FloatField(verbose_name='GDP', null=True, blank=True)
    gnipc = models.IntegerField(verbose_name='GNI/CAPITA', null=True, blank=True)
    life_expectancy = models.IntegerField(null=True, blank=True)
    urban_population = models.FloatField(
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        verbose_name='Urban POP (%)',
        null=True, blank=True,
    )
    poverty = models.FloatField(
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        verbose_name='Poverty (%)',
        null=True, blank=True,
    )
    literacy = models.FloatField(
        validators=[MaxValueValidator(100), MinValueValidator(0)],
        verbose_name='Literacy (%)',
        null=True, blank=True,
    )

    # National Society Indicators (Using Script: FDRS API)
    income = models.FloatField(verbose_name='Income (CHF)', null=True, blank=True)
    expenditures = models.FloatField(verbose_name='Expenditures (CHF)', null=True, blank=True)
    volunteers = models.IntegerField(null=True, blank=True)
    trained_in_first_aid = models.IntegerField(null=True, blank=True)

    # Key Climate Event (Manual Entry)
    avg_temperature = models.FloatField(null=True, blank=True)
    avg_rainfall_precipitation = models.FloatField(null=True, blank=True)
    rainy_season = models.CharField(choices=Status.CHOICES, max_length=20, blank=True, null=True)

    # JSON DATA (Using Script)
    fts_data = JSONField(default=list)
    start_network_data = JSONField(default=list)
    past_crises_events = JSONField(default=list)
    past_epidemics = JSONField(default=list)
    inform_indicators = JSONField(default=list)

    def __str__(self):
        return str(self.country)

    @property
    def appeals(self):
        return Appeal.objects.filter(country=self.country).all()

    @property
    def past_crises_events_count(self):
        return self.pastcrisesevent_set.count()


class SocialEvent(models.Model):
    overview = models.ForeignKey(CountryOverview, on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ('overview', 'label')

    def __str__(self):
        return f'{self.overview} - {self.label}: {self.value}'


class KeyClimateEvent(models.Model):
    overview = models.ForeignKey(CountryOverview, on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now=True)

    month = models.PositiveSmallIntegerField(choices=Month.CHOICES)
    # TODO: Add validation min < max
    avg_max_temperature = models.FloatField()
    avg_min_temperature = models.FloatField()
    avg_rainfall_precipitation = models.FloatField()

    class Meta:
        unique_together = ('overview', 'month')

    def __str__(self):
        return f'{self.overview.country} - {self.get_month_display()}'


class SeasonalCalender(models.Model):
    overview = models.ForeignKey(CountryOverview, on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=20)  # TODO: CHOICES?
    sector = models.CharField(max_length=20)  # TODO: CHOICES?
    date_start = models.DateField()
    date_end = models.DateField()

    class Meta:
        unique_together = ('overview', 'sector', 'title')

    def __str__(self):
        return f'{self.overview.country} - {self.title} - {self.sector}'
