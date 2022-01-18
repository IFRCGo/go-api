from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import Action, ActionOrg, ActionType


class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(label=_('organizations'), choices=ActionOrg.CHOICES)
    field_report_types = forms.MultipleChoiceField(label=_('field report types'), choices=ActionType.CHOICES)

    class Meta:
        model = Action
        fields = '__all__'
