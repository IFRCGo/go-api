from django import forms

from .models import Action, ActionOrg

class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(choices=ActionOrg.CHOICES)

    class Meta:
        model = Action
        fields = '__all__'
