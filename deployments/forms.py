import io
import traceback
import datetime
import csv

from django import forms
from django.utils.safestring import mark_safe
from django.contrib import messages

from api.models import Country, District

from .widgets import EnumArrayWidget
from .models import (
    Project,
    ProjectImport,
    OperationTypes,
    ProgrammeTypes,
    Sectors,
    SectorTags,
    Statuses,
)


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


class ProjectImportForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'accept': '.csv'}))

    def _handle_bulk_upload(self, user, file):
        def strip_date(date):
            return datetime.datetime.strptime(date, "%Y-%m-%d").date()

        file.seek(0)
        reader = csv.DictReader(io.StringIO(file.read().decode('utf-8', errors='ignore')), skipinitialspace=True)
        projects = []

        # Enum options
        operation_types = {label.lower(): value for value, label in OperationTypes.choices()}
        programme_types = {label.lower(): value for value, label in ProgrammeTypes.choices()}
        sectors = {label.lower(): value for value, label in Sectors.choices()}
        sector_tags = {label.lower(): value for value, label in SectorTags.choices()}
        statuses = {label.lower(): value for value, label in Statuses.choices()}

        for row in reader:
            # TODO: Try to do this in a single query
            reporting_ns = Country.objects.filter(name__iexact=row['Supporting NS'].strip()).first()
            project_district = District.objects.filter(
                country__name__iexact=row['Country'].strip(),
                name__iexact=row['Region'].strip(),
            ).first()

            projects.append(Project(
                user=user,
                reporting_ns=reporting_ns,
                project_district=project_district,

                # Enum fields
                operation_type=operation_types[row['Operation type'].lower().strip()],
                programme_type=programme_types[row['Programme Type'].lower().strip()],
                primary_sector=sectors[row['Primary Sector'].lower().strip()],
                secondary_sectors=[sector_tags[tag.lower().strip()] for tag in row['Tags'].split(',')],
                status=statuses[row['Status'].lower().strip()],

                name=row['Project Name'],
                start_date=strip_date(row['Start Date']),
                end_date=strip_date(row['End Date']),
                budget_amount=row['Budget(CHF)'],

                # Optional fields
                target_male=row['Targeted Males'],
                target_female=row['Targeted Females'],
                target_other=row['Targeted Others'],
                target_total=row['Targeted Total'],
                reached_male=row['Reached Males'],
                reached_female=row['Reached Females'],
                reached_other=row['Reached Others'],
                reached_total=row['Reached Total'],
            ))
        return Project.objects.bulk_create(projects)

    def handle_bulk_upload(self, request):
        file = self.cleaned_data['file']
        project_import = ProjectImport.objects.create(
            created_by=request.user,
            file=file,
        )

        try:
            projects = self._handle_bulk_upload(request.user, file)
            project_import.projects_created.add(*projects)
            project_import.message = f'Successfully added <b>{len(projects)}</b> project(s) using <b>{file}</b>.'
            project_import.status = ProjectImport.SUCCESS
            # Also show error in Admin Panel
            messages.add_message(request, messages.INFO, mark_safe(project_import.message))
        except Exception:
            project_import.message = (
                f"Importing <b>{file}</b> failed. Check file and try again!!<br />"
                f"<pre>{traceback.format_exc()}</pre>"
            )
            messages.add_message(request, messages.ERROR, mark_safe(project_import.message))
            project_import.status = ProjectImport.FAILURE
        project_import.save()
