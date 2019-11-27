from django import forms

from .models import Action, ActionOrg, ActionType

class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(choices=ActionOrg.CHOICES)
    field_report_types = forms.MultipleChoiceField(choices=ActionType.CHOICES)

    class Meta:
        model = Action
        fields = '__all__'
