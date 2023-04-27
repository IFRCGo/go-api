import io
import traceback
import csv
import datetime
from functools import reduce
from itertools import zip_longest

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.db.models import Q
from django.core.exceptions import ValidationError
from api.logger import logger

from api.models import (
    Country,
    District,
    DisasterType,
)

from .models import (
    Project,
    ProjectImport,
    OperationTypes,
    ProgrammeTypes,
    Sector,
    SectorTag,
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
        operation_types = {label for _, label in OperationTypes.choices}
        programme_types = {label for _, label in ProgrammeTypes.choices}
        sectors = Sector.objects.values_list('title', flat=True)
        sector_tags = SectorTag.objects.values_list('title', flat=True)
        statuses = {label for _, label in Statuses.choices}

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
        def _get_error_message(row, custom_errors, validation_errors=None):
            messages = ', '.join([
                f"{field}: {', '.join(error_message)}"
                for field, error_message in {
                    **(validation_errors or {}),
                    **custom_errors,
                }.items()
            ])
            return f'ROW {row}: {str(messages)}'

        def _key_clean(string):
            return string.lower().strip()

        def _parse_date(date, field, row_errors):
            try:
                return datetime.datetime.strptime(date, '%d/%m/%Y')
            except ValueError as e:
                row_errors[field] = [str(e)]

        def _parse_integer(integer):
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
        operation_types = {label.lower(): value for value, label in OperationTypes.choices}
        programme_types = {label.lower(): value for value, label in ProgrammeTypes.choices}
        statuses = {label.lower(): value for value, label in Statuses.choices}

        # Not enums, but maybe could be used later to avoid multiple queries for id-s: FIXME
        # sectors = {t.title.lower(): t.id for t in Sector.objects.all()}
        # sector_tags = {t.title.lower(): t.id for t in SectorTag.objects.all()}
        # disaster_types ?

        c = self.Columns

        # Extract from import csv file
        for row_number, row in enumerate(reader, start=2):
            district_names = [
                d.strip() for d in row[c.DISTRICT].split(',')
            ] if row[c.DISTRICT].lower() not in ['countrywide', ''] else []
            reporting_ns_name = row[c.REPORTING_NS].strip()
            country_name = row[c.COUNTRY].strip()
            disaster_type_name = row[c.DISASTER_TYPE].strip()
            sector_name = row[c.PRIMARY_SECTOR].strip()
            tag_names = [
                d.strip() for d in row[c.TAGS].split(',')
            ]

            reporting_ns = Country.objects.filter(
                Q(name__iexact=reporting_ns_name) | Q(society_name__iexact=reporting_ns_name)
            ).first()
            project_sector = Sector.objects.filter(title=sector_name).first()
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
                # Check if all district_names is available in db
                if len(project_districts) == len(district_names):
                    project_country = project_districts[0].country
                else:
                    project_country = None
                    # A validation error will be raised. This is just a custom message
                    row_errors['project_districts'] = ['Given districts/regions are not available.']

            project_sectortags = []
            if tag_names:
                project_sectortags = list(SectorTag.objects.filter(
                    reduce(lambda acc, item: acc | item,
                        [Q(title=title) for title in tag_names],
                          )
                ).all())
                # Check if all tag_names is available in db
                if len(project_sectortags) != len(tag_names):
                    # A validation error will be raised. This is just a custom message
                    row_errors['project_sectortags'] = [f'Given tags: "{tag_names}" are not all available.']

            if reporting_ns is None:
                row_errors['reporting_ns'] = [f'Given country "{reporting_ns_name}" is not available.']
            if disaster_type is None:
                row_errors['disaster_type'] = [f'Given disaster type "{disaster_type_name}" is not available.']

            project = Project(
                user=user,
                reporting_ns=reporting_ns,
                project_country=project_country,
                # project_districts and secondary_sectors are M2M fields, they will be added later.
                dtype=disaster_type,

                # Enum fields
                operation_type=operation_types.get(_key_clean(row[c.OPERATION_TYPE])),
                programme_type=programme_types.get(_key_clean(row[c.PROGRAMME_TYPE])),
                primary_sector=project_sector,
                status=statuses.get(_key_clean(row[c.STATUS])),

                name=row[c.PROJECT_NAME],
                start_date=_parse_date(row[c.START_DATE], 'start_date', row_errors),
                end_date=_parse_date(row[c.END_DATE], 'end_date', row_errors),
                budget_amount=_parse_integer(row[c.BUDGET]),

                # Optional fields
                target_male=_parse_integer(row[c.TARGETED_MALES]),
                target_female=_parse_integer(row[c.TARGETED_FEMALES]),
                target_other=_parse_integer(row[c.TARGETED_OTHER]),
                target_total=_parse_integer(row[c.TARGETED_TOTAL]),
                reached_male=_parse_integer(row[c.REACHED_MALES]),
                reached_female=_parse_integer(row[c.REACHED_FEMALES]),
                reached_other=_parse_integer(row[c.REACHED_OTHERS]),
                reached_total=_parse_integer(row[c.REACHED_TOTAL]),
            )
            try:
                project.full_clean()
                if len(row_errors) == 0:
                    projects.append([project, project_districts, project_sectortags])
                else:
                    errors.append(_get_error_message(row_number, row_errors))
            except ValidationError as e:
                errors.append(_get_error_message(row_number, row_errors, e.message_dict))

        if len(errors) != 0:
            errors_str = '\n'.join(errors)
            raise Exception(f"Error detected:\n{errors_str}")

        Project.objects.bulk_create([p[0] for p in projects])
        # Set M2M Now
        for project, project_districts, project_sectortags in projects:
            project.project_districts.set(project_districts)
            project.secondary_sectors.set(project_sectortags)
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
            project_import.status = ProjectImport.ProjImpStatus.SUCCESS
            # Also show error in Admin Panel
            messages.add_message(request, messages.INFO, mark_safe(project_import.message))
        except Exception as e:
            project_import.message = (
                f"Importing <b>{file}</b> failed. Check file and try again!!<br />"
                f"<pre>{traceback.format_exc()}</pre>"
            )
            if isinstance(e, KeyError):
                project_import.message += (
                    "<pre>NOTE: Make sure to use correct <b>file delimiter</b> and <b>string delimiter!</b></pre>"
                )
            messages.add_message(request, messages.ERROR, mark_safe(project_import.message))
            project_import.status = ProjectImport.ProjImpStatus.FAILURE
        project_import.save()
