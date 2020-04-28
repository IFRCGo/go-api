import io
import dateutil.parser
import traceback
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
        def key_clean(string):
            return string.lower().strip()

        def parse_date(date):
            return dateutil.parser.parse(date)

        def parse_integer(integer):
            try:
                if isinstance(integer, str):
                    return int(integer.replace(',', ''))
                return integer
            except ValueError:
                return None

        file.seek(0)
        reader = csv.DictReader(io.StringIO(file.read().decode('utf-8', errors='ignore')), skipinitialspace=True)
        projects = []

        # Enum options
        operation_types = {label.lower(): value for value, label in OperationTypes.choices()}
        programme_types = {label.lower(): value for value, label in ProgrammeTypes.choices()}
        sectors = {label.lower(): value for value, label in Sectors.choices()}
        sector_tags = {label.lower(): value for value, label in SectorTags.choices()}
        statuses = {label.lower(): value for value, label in Statuses.choices()}

        # Handle Custom Sectors/Tags for Health (Keys all lower)
        sectors.update({
            'health': Sectors.HEALTH_PUBLIC,
            'health (public)': Sectors.HEALTH_PUBLIC,
            'health (clinical)': Sectors.HEALTH_CLINICAL,
        })
        sector_tags.update({
            'health': SectorTags.HEALTH_PUBLIC,
            'health (public)': SectorTags.HEALTH_PUBLIC,
            'health (clinical)': SectorTags.HEALTH_CLINICAL,
        })

        # Extract from import csv file
        for row in reader:
            # TODO: Try to do this in a single query
            district_name = row['Region'].strip()
            reporting_ns_name = row['Supporting NS'].strip()
            country_name = row['Country'].strip()

            reporting_ns = Country.objects.filter(name__iexact=reporting_ns_name).first()
            if district_name.lower() in ['countrywide', '']:
                project_country = Country.objects.filter(name__iexact=country_name).first()
                project_district = None
            else:
                project_district = District.objects.filter(
                    country__name__iexact=country_name,
                    name__iexact=district_name,
                ).first()
                project_country = project_district.country

            projects.append(Project(
                user=user,
                reporting_ns=reporting_ns,
                project_district=project_district,
                project_country=project_country,

                # Enum fields
                operation_type=operation_types[key_clean(row['Operation type'])],
                programme_type=programme_types[key_clean(row['Programme Type'])],
                primary_sector=sectors[key_clean(row['Primary Sector'])],
                secondary_sectors=[
                    sector_tags[key_clean(tag)] for tag in row['Tags'].split(',') if key_clean(tag) in sector_tags
                ],
                status=statuses[key_clean(row['Status'])],

                name=row['Project Name'],
                start_date=parse_date(row['Start Date']),
                end_date=parse_date(row['End Date']),
                budget_amount=row['Budget(CHF)'],

                # Optional fields
                target_male=parse_integer(row['Targeted Males']),
                target_female=parse_integer(row['Targeted Females']),
                target_other=parse_integer(row['Targeted Others']),
                target_total=parse_integer(row['Targeted Total']),
                reached_male=parse_integer(row['Reached Males']),
                reached_female=parse_integer(row['Reached Females']),
                reached_other=parse_integer(row['Reached Others']),
                reached_total=parse_integer(row['Reached Total']),
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
