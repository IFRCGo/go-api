import io
import dateutil.parser
import traceback
import csv

from django import forms
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import ValidationError

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
            choices=SectorTags.choices(),
        )


class ProjectImportForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'accept': '.csv'}))
    field_delimiter = forms.CharField(initial=';')
    string_delimiter = forms.CharField(initial='"')

    def _handle_bulk_upload(self, user, file, delimiter, quotechar):
        def key_clean(string):
            return string.lower().strip()

        def parse_date(date):
            return dateutil.parser.parse(date)

        def parse_integer(integer):
            try:
                if isinstance(integer, str):
                    # ALL are integer fields. Change this if not
                    return int(float(integer.replace(',', '')))
                return integer
            except ValueError:
                return None

        file.seek(0)
        reader = csv.DictReader(
            io.StringIO(file.read().decode('utf-8-sig', errors='ignore')),
            skipinitialspace=True,
            delimiter=delimiter,
            quotechar=quotechar,
        )
        errors = []
        projects = []

        # Enum options
        operation_types = {label.lower(): value for value, label in OperationTypes.choices()}
        programme_types = {label.lower(): value for value, label in ProgrammeTypes.choices()}
        sectors = {label.lower(): value for value, label in Sectors.choices()}
        sector_tags = {label.lower(): value for value, label in SectorTags.choices()}
        statuses = {label.lower(): value for value, label in Statuses.choices()}

        # COLUMNS
        COUNTRY_COL = 'Country'
        DISTRICT_COL = 'Region'
        REPORTING_NS_COL = 'Supporting NS'
        OPERATION_TYPE_COL = 'Operation type'
        PROGRAMME_TYPE_COL = 'Programme Type'
        PRIMARY_SECTOR_COL = 'Primary Sector'
        TAGS_COL = 'Tags'
        STATUS_COL = 'Status'
        PROJECT_NAME_COL = 'Project Name'
        START_DATE_COL = 'Start Date'
        END_DATE_COL = 'End Date'
        BUDGET_COL = 'Budget(CHF)'
        TARGETED_MALES_COL = 'Targeted Males'
        TARGETED_FEMALES_COL = 'Targeted Females'
        TARGETED_OTHER_COL = 'Targeted Others'
        TARGETED_TOTAL_COL = 'Targeted Total'
        REACHED_MALES_COL = 'Reached Males'
        REACHED_FEMALES_COL = 'Reached Females'
        REACHED_OTHERS_COL = 'Reached Others'
        REACHED_TOTAL = 'Reached Total'

        # Extract from import csv file
        for row_number, row in enumerate(reader):
            # TODO: Try to do this in a single query
            district_name = row[DISTRICT_COL].strip()
            reporting_ns_name = row[REPORTING_NS_COL].strip()
            country_name = row[COUNTRY_COL].strip()

            reporting_ns = Country.objects.filter(
                Q(name__iexact=reporting_ns_name) | Q(society_name__iexact=reporting_ns_name)
            ).first()

            row_errors = {}
            if district_name is None or district_name.lower() in ['countrywide', '']:
                project_country = Country.objects.filter(name__iexact=country_name).first()
                project_district = None
                if project_country is None:
                    row_errors['project_country'] = [f'Given country "{country_name}" is not available.']
            else:
                project_district = District.objects.filter(
                    (Q(country_name__iexact=country_name) | Q(country__name__iexact=country_name)),
                    name__iexact=district_name,
                ).first()
                if project_district is not None:
                    project_country = project_district.country
                else:
                    # A validation error will be raised. This is just a custom message
                    row_errors['project_country'] = ['Given district/region is not available.']

            project = Project(
                user=user,
                reporting_ns=reporting_ns,
                project_district=project_district,
                project_country=project_country,

                # Enum fields
                operation_type=operation_types.get(key_clean(row[OPERATION_TYPE_COL])),
                programme_type=programme_types.get(key_clean(row[PROGRAMME_TYPE_COL])),
                primary_sector=sectors.get(key_clean(row[PRIMARY_SECTOR_COL])),
                secondary_sectors=[
                    sector_tags.get(key_clean(tag)) for tag in row[TAGS_COL].split(',') if key_clean(tag) in sector_tags
                ],
                status=statuses.get(key_clean(row[STATUS_COL])),

                name=row[PROJECT_NAME_COL],
                start_date=parse_date(row[START_DATE_COL]),
                end_date=parse_date(row[END_DATE_COL]),
                budget_amount=parse_integer(row[BUDGET_COL]),

                # Optional fields
                target_male=parse_integer(row[TARGETED_MALES_COL]),
                target_female=parse_integer(row[TARGETED_FEMALES_COL]),
                target_other=parse_integer(row[TARGETED_OTHER_COL]),
                target_total=parse_integer(row[TARGETED_TOTAL_COL]),
                reached_male=parse_integer(row[REACHED_MALES_COL]),
                reached_female=parse_integer(row[REACHED_FEMALES_COL]),
                reached_other=parse_integer(row[REACHED_OTHERS_COL]),
                reached_total=parse_integer(row[REACHED_TOTAL]),
            )
            try:
                project.full_clean()
                projects.append(project)
            except ValidationError as e:
                messages = ', '.join([
                    f"{field}: {', '.join(row_errors.get(field, error_message))}"
                    for field, error_message in e.message_dict.items()
                ])
                errors.append(f'ROW {row_number+2}: {str(messages)}')

        if len(errors) != 0:
            errors_str = '\n'.join(errors)
            raise Exception(f"Error detected:\n{errors_str}")
        return Project.objects.bulk_create(projects)

    def handle_bulk_upload(self, request):
        file = self.cleaned_data['file']
        delimiter = self.cleaned_data['field_delimiter']
        quotechar = self.cleaned_data['string_delimiter']
        project_import = ProjectImport.objects.create(
            created_by=request.user,
            file=file,
        )

        try:
            projects = self._handle_bulk_upload(request.user, file, delimiter, quotechar)
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
