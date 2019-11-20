from django import forms

from .models import Action, ACTION_ORG_CHOICES

class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(choices=ACTION_ORG_CHOICES)

    class Meta:
        model = Action
        fields = '__all__'
