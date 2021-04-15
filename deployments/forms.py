import io
import dateutil.parser
import traceback
import csv
from functools import reduce
from itertools import zip_longest

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.db.models.functions import Coalesce

from api.models import (
    Country,
    District,
    DisasterType,
)

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
    file = forms.FileField(label=_('file'), widget=forms.FileInput(attrs={'accept': '.csv'}))
    field_delimiter = forms.CharField(label=_('file delimiter'), initial=';')
    string_delimiter = forms.CharField(label=_('string delimiter'), initial='"')

    class Columns:
        # COLUMNS
        COUNTRY = 'Country'
        DISTRICT = 'Regions'
        REPORTING_NS = 'Reporting NS'
        DISASTER_TYPE = 'Disaster Type'
        OPERATION_TYPE = 'Operation Type'
        PROGRAMME_TYPE = 'Programme Type'
        PRIMARY_SECTOR = 'Primary Sector'
        TAGS = 'Tags'
        STATUS = 'Status'
        PROJECT_NAME = 'Project Name'
        START_DATE = 'Start Date'
        END_DATE = 'End Date'
        BUDGET = 'Budget(CHF)'
        TARGETED_MALES = 'Targeted Males'
        TARGETED_FEMALES = 'Targeted Females'
        TARGETED_OTHER = 'Targeted Others'
        TARGETED_TOTAL = 'Targeted Total'
        REACHED_MALES = 'Reached Males'
        REACHED_FEMALES = 'Reached Females'
        REACHED_OTHERS = 'Reached Others'
        REACHED_TOTAL = 'Reached Total'

    @classmethod
    def generate_template(cls):
        country_districts = list(
            District.objects
            .values_list('country__name', 'name')
            .order_by('country__name', 'name')
        )
        countries = Country.objects.values_list('name', flat=True)
        disaster_types = DisasterType.objects.values_list('name', flat=True)
        operation_types = {label for _, label in OperationTypes.choices()}
        programme_types = {label for _, label in ProgrammeTypes.choices()}
        sectors = {label for _, label in Sectors.choices()}
        sector_tags = {label for _, label in SectorTags.choices()}
        statuses = {label for _, label in Statuses.choices()}

        # Headers
        c = cls.Columns
        headers = [
            c.COUNTRY,
            c.DISTRICT,
            c.REPORTING_NS,
            c.DISASTER_TYPE,
            c.OPERATION_TYPE,
            c.PROGRAMME_TYPE,
            c.PRIMARY_SECTOR,
            c.TAGS,
            c.STATUS,
            c.PROJECT_NAME,
            c.START_DATE,
            c.END_DATE,
            c.BUDGET,
            c.TARGETED_MALES,
            c.TARGETED_FEMALES,
            c.TARGETED_OTHER,
            c.TARGETED_TOTAL,
            c.REACHED_MALES,
            c.REACHED_FEMALES,
            c.REACHED_OTHERS,
            c.REACHED_TOTAL,
        ]

        rows = [
            headers,
            # Valid values
            *zip_longest(
                [c[0] for c in country_districts],  # Countries
                [c[1] for c in country_districts],  # Regions/Districts
                countries,
                disaster_types,
                operation_types,
                programme_types,
                sectors,
                sector_tags,
                statuses,
            )
        ]
        return rows

    def _handle_bulk_upload(self, user, file, delimiter, quotechar):
        def get_error_message(row, custom_errors, validation_erorrs=None):
            messages = ', '.join([
                f"{field}: {', '.join(error_message)}"
                for field, error_message in {
                    **(validation_erorrs or {}),
                    **custom_errors,
                }.items()
            ])
            return f'ROW {row}: {str(messages)}'

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

        c = self.Columns
        # Extract from import csv file
        for row_number, row in enumerate(reader, start=2):
            district_names = [
                d for d in row[c.DISTRICT].strip().split(';')
                if d.lower() not in ['countrywide', '']
            ]
            reporting_ns_name = row[c.REPORTING_NS].strip()
            country_name = row[c.COUNTRY].strip()
            disaster_type_name = row[c.DISASTER_TYPE].strip()

            reporting_ns = Country.objects.filter(
                Q(name__iexact=reporting_ns_name) | Q(society_name__iexact=reporting_ns_name)
            ).first()
            disaster_type = DisasterType.objects.filter(name__iexact=disaster_type_name).first()

            row_errors = {}
            project_districts = []
            if len(district_names) == 0:
                project_country = Country.objects.filter(name__iexact=country_name).first()
                if project_country is None:
                    row_errors['project_country'] = [f'Given country "{country_name}" is not available.']
                else:
                    project_districts = list(project_country.district_set.all())

                if len(project_districts) == 0:
                    row_errors['project_districts'] = [f'There is no district for given country "{country_name}" in database.']
            else:
                project_districts = list(District.objects.filter(
                    reduce(
                        lambda acc, item: acc | item,
                        [
                            Q(country__name__iexact=country_name) & Q(name__iexact=district_name)
                            for district_name in district_names
                        ],
                    )
                ).all())
                # Check if all district_names is avaliable in db
                if len(project_districts) == len(district_names):
                    project_country = project_districts[0].country
                else:
                    # A validation error will be raised. This is just a custom message
                    row_errors['project_districts'] = ['Given districts/regions are not available.']

            if reporting_ns is None:
                row_errors['reporting_ns'] = [f'Given country "{reporting_ns_name}" is not available.']
            if disaster_type is None:
                row_errors['disaster_type'] = [f'Given disaster type "{disaster_type_name}" is not available.']

            project = Project(
                user=user,
                reporting_ns=reporting_ns,
                project_country=project_country,
                # project_districts is M2M field so it will be added later
                dtype=disaster_type,

                # Enum fields
                operation_type=operation_types.get(key_clean(row[c.OPERATION_TYPE])),
                programme_type=programme_types.get(key_clean(row[c.PROGRAMME_TYPE])),
                primary_sector=sectors.get(key_clean(row[c.PRIMARY_SECTOR])),
                secondary_sectors=[
                    sector_tags.get(key_clean(tag)) for tag in row[c.TAGS].split(',') if key_clean(tag) in sector_tags
                ],
                status=statuses.get(key_clean(row[c.STATUS])),

                name=row[c.PROJECT_NAME],
                start_date=parse_date(row[c.START_DATE]),
                end_date=parse_date(row[c.END_DATE]),
                budget_amount=parse_integer(row[c.BUDGET]),

                # Optional fields
                target_male=parse_integer(row[c.TARGETED_MALES]),
                target_female=parse_integer(row[c.TARGETED_FEMALES]),
                target_other=parse_integer(row[c.TARGETED_OTHER]),
                target_total=parse_integer(row[c.TARGETED_TOTAL]),
                reached_male=parse_integer(row[c.REACHED_MALES]),
                reached_female=parse_integer(row[c.REACHED_FEMALES]),
                reached_other=parse_integer(row[c.REACHED_OTHERS]),
                reached_total=parse_integer(row[c.REACHED_TOTAL]),
            )
            try:
                project.full_clean()
                if len(row_errors) == 0:
                    projects.append([project, project_districts])
                else:
                    errors.append(get_error_message(row_number, row_errors))
            except ValidationError as e:
                errors.append(get_error_message(row_number, row_errors, e.message_dict))

        if len(errors) != 0:
            errors_str = '\n'.join(errors)
            raise Exception(f"Error detected:\n{errors_str}")

        Project.objects.bulk_create([p[0] for p in projects])
        # Set M2M Now
        for project, project_districts in projects:
            project.project_districts.set(project_districts)
        # Return projects for ProjectImport
        return [p[0] for p in projects]

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
