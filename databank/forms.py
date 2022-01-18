from django import forms
from django.utils.translation import ugettext

from .models import CountryOverview, SeasonalCalender


class CountryOverviewForm(forms.ModelForm):
    class Meta:
        model = CountryOverview
        fields = '__all__'


class SeasonalCalenderForm(forms.ModelForm):
    def clean_date_end(self):
        start = self.cleaned_data['date_start']
        end = self.cleaned_data['date_end']
        if start >= end:
            raise forms.ValidationError(ugettext('Invalid End Date'))
        return end

    class Meta:
        model = SeasonalCalender
        fields = '__all__'
