from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import InformalAction
from api.models import ActionOrg, ActionType


class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(label=_('organizations'), choices=ActionOrg.CHOICES)
    informal_update_types = forms.MultipleChoiceField(label=_('informal update types'), choices=ActionType.CHOICES)

    class Meta:
        model = InformalAction
        fields = '__all__'
