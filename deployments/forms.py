from django import forms

from .widgets import EnumArrayWidget
from .models import Project, Sectors


class ProjectForm(forms.ModelForm):
    """
    Custom Form For Project
    - secondary_sectors: Array EnumField
    """

    class Meta:
        model = Project
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['secondary_sectors'].widget = EnumArrayWidget(
            choices=Sectors.choices(),
        )
