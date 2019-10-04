from django import forms

from .models import Project, Sectors


class ProjectForm(forms.ModelForm):
    """
    Custom Form For Project
    - secondary_sectors: Array EnumField
    """
    secondary_sectors = forms.MultipleChoiceField(choices=Sectors.choices, required=False)

    class Meta:
        model = Project
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secondary_sectors = {str(s.value): s for s in Sectors}
        self.initial['secondary_sectors'] = [s.value for s in self.initial.get('secondary_sectors', [])]

    def clean_secondary_sectors(self):
        primary_sector = str(self.cleaned_data['primary_sector'].value)
        return [
            self.secondary_sectors[v]
            for v in self.cleaned_data['secondary_sectors']
            if (
                v in self.secondary_sectors and
                v != primary_sector
            )
        ]

    def save(self, commit=True):
        return super().save(commit=commit)
