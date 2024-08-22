from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Action, ActionOrg, ActionType


class ActionForm(forms.ModelForm):
    organizations = forms.MultipleChoiceField(label=_("organizations"), choices=ActionOrg.choices)
    field_report_types = forms.MultipleChoiceField(label=_("field report types"), choices=ActionType.choices)

    class Meta:
        model = Action
        fields = "__all__"


class RichSummary(forms.ModelForm):
    class Meta:
        widgets = {
            "summary_en": forms.Textarea(attrs={"class": "richtext"}),
            "summary_es": forms.Textarea(attrs={"class": "richtext"}),
            "summary_fr": forms.Textarea(attrs={"class": "richtext"}),
            "summary_ar": forms.Textarea(attrs={"class": "richtext"}),
        }


class RichDescription(forms.ModelForm):
    class Meta:
        widgets = {
            "description_en": forms.Textarea(attrs={"class": "richtext"}),
            "description_es": forms.Textarea(attrs={"class": "richtext"}),
            "description_fr": forms.Textarea(attrs={"class": "richtext"}),
            "description_ar": forms.Textarea(attrs={"class": "richtext"}),
        }


class RichSitOverview(forms.ModelForm):
    class Meta:
        widgets = {
            "situational_overview_en": forms.Textarea(attrs={"class": "richtext"}),
            "situational_overview_es": forms.Textarea(attrs={"class": "richtext"}),
            "situational_overview_fr": forms.Textarea(attrs={"class": "richtext"}),
            "situational_overview_ar": forms.Textarea(attrs={"class": "richtext"}),
        }
