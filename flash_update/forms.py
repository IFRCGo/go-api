from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import FlashAction
from api.models import ActionOrg, ActionType


class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(label=_('organizations'), choices=ActionOrg.CHOICES)
    Flash_update_types = forms.MultipleChoiceField(label=_('flash update types'), choices=ActionType.CHOICES)

    class Meta:
        model = FlashAction
        fields = '__all__'
