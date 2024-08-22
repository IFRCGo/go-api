from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Action, ActionOrg, ActionType


class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(label=_("organizations"), choices=ActionOrg.choices)
    field_report_types = forms.MultipleChoiceField(label=_("field report types"), choices=ActionType.choices)

    class Meta:
        model = Action
        fields = "__all__"


class SocietyNameOverviewPlain(forms.ModelForm):
    class Meta:
        widgets = {
            "society_name_en": forms.Textarea(attrs={"class": "plain-textarea"}),
            "society_name_es": forms.Textarea(attrs={"class": "plain-textarea"}),
            "society_name_fr": forms.Textarea(attrs={"class": "plain-textarea"}),
            "society_name_ar": forms.Textarea(attrs={"class": "plain-textarea"}),
            "overview_en": forms.Textarea(attrs={"class": "plain-textarea"}),
            "overview_es": forms.Textarea(attrs={"class": "plain-textarea"}),
            "overview_fr": forms.Textarea(attrs={"class": "plain-textarea"}),
            "overview_ar": forms.Textarea(attrs={"class": "plain-textarea"}),
        }


class SummaryPlain(forms.ModelForm):
    class Meta:
        widgets = {
            "summary_en": forms.Textarea(attrs={"class": "plain-textarea"}),
            "summary_es": forms.Textarea(attrs={"class": "plain-textarea"}),
            "summary_fr": forms.Textarea(attrs={"class": "plain-textarea"}),
            "summary_ar": forms.Textarea(attrs={"class": "plain-textarea"}),
        }


class DescriptionPlain(forms.ModelForm):
    class Meta:
        widgets = {
            "description": forms.Textarea(attrs={"class": "plain-textarea"}),
        }
