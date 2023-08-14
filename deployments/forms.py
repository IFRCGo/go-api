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
from api.models import (
    Country,
    District,
    DisasterType,
    VisibilityCharChoices,
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
    field_delimiter = forms.CharField(label=_('field delimiter'), initial=',')
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
        VISIBILITY = 'Visibility'
        ACTUAL_EXPENDITURE = 'Actual Expenditure'
        REPORTING_NS_CONTACT_EMAIL = 'Contact Email'
        REPORTING_NS_CONTACT_NAME = 'Contact Name'
        REPORTING_NS_CONTACT_ROLE = 'Contact Role'
        DESCRIPTION = 'Description'

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
            c.VISIBILITY,
            c.ACTUAL_EXPENDITURE,
            c.REPORTING_NS_CONTACT_EMAIL,
            c.REPORTING_NS_CONTACT_NAME,
            c.REPORTING_NS_CONTACT_ROLE,
            c.DESCRIPTION
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
                    return int(integer)
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

        # Not enums, but can be used to avoid multiple queries for foreign key id-s
        sectors = {t.title.lower(): t.id for t in Sector.objects.all()}
        add_to_sectors = dict()  # Add the main words of sectors to the definition:
        for s in sectors.keys():
            tt = s.replace(' and', '').replace(', ', ',').replace(' ', ',').split(',')
            for t in tt:
                add_to_sectors[t] = sectors[s]
        sectors.update(add_to_sectors)
        sector_tags = {t.title.lower(): t.id for t in SectorTag.objects.all()}
        disaster_types = {t.name.lower(): t.id for t in DisasterType.objects.all()}
        visibilities = {t.label: t.value for t in VisibilityCharChoices}

        c = self.Columns

        # Extract from import csv file
        for row_number, row in enumerate(reader, start=2):
            district_names = list({d.strip() for d in filter(
                lambda x: x.strip() != '', row[c.DISTRICT].split(','))
            }) if row[c.DISTRICT].lower() not in ['countrywide', ''] else []
            reporting_ns_name = row[c.REPORTING_NS].strip()
            country_name = row[c.COUNTRY].strip()
            # An often misspelled word cleanup:
            if reporting_ns_name == 'Turkey':
                reporting_ns_name = 'Türkiye'
            if country_name == 'Turkey':
                country_name = 'Türkiye'
            disaster_type_name = row[c.DISASTER_TYPE].strip()
            sector_name = row[c.PRIMARY_SECTOR].strip()
            tag_names = list({d.strip() for d in filter(
                lambda x: x.strip() != '', row[c.TAGS].split(','))
            })

            reporting_ns = Country.objects.filter(
                Q(name__iexact=reporting_ns_name) | Q(society_name__iexact=reporting_ns_name)
            ).first()

            # Cheaper than:     Sector.objects.filter(title=sector_name).first()
            project_sector_id = sectors[sector_name.lower()] if sector_name else None
            # Cheaper than:    DisasterType.objects.filter(name__iexact=disaster_type_name).first()
            disaster_type_id = disaster_types[disaster_type_name.lower()] if disaster_type_name else None

            row_errors = {}
            project_country = Country.objects.filter(name__iexact=country_name).first()
            project_districts = []
            if district_names:
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
                    if project_country is None:  # in case of we did not find a proper country name, trying to know it:
                        project_country = project_districts[0].country
                else:
                    # but it can not happen that some of the given district-names cannot be found:
                    row_errors['project_districts'] = [f'Some given district_names are not available. "{district_names}"']

            # A validation error will be raised. This is just a custom message
            if project_country is None:
                row_errors['project_country'] = [f'Country "{country_name}" is not available.']

            project_sectortag_ids = []  # if we use sectortag objects, not only id-s, the "project_sectortags" would be better.
            if tag_names:
                all_ok = True
                for t in tag_names:
                    if t.lower() not in sector_tags:
                        all_ok = False
                        row_errors['project_sectortags'] = [f'Given tag: "{t}" is not all available.']
                if all_ok:
                    # Cheaper than: list(SectorTag.objects.filter(reduce(lambda acc, item: acc | item, [Q(title=title) for title in tag_names],)).all())
                    project_sectortag_ids = {title: sector_tags[title.lower()] for title in tag_names}.values()

            if reporting_ns is None:
                row_errors['reporting_ns'] = [f'Given country "{reporting_ns_name}" is not available.']
            # Optional, but can be invalid
            if disaster_type_id is None and disaster_type_name != '':
                row_errors['disaster_type'] = [f'Given disaster type "{disaster_type_name}" is not available.']
            visibility = row[c.VISIBILITY].strip()

            project = Project(
                user=user,
                reporting_ns=reporting_ns,
                project_country=project_country,
                # project_districts and secondary_sectors are M2M fields, they will be added later.
                primary_sector_id=project_sector_id,
                dtype_id=disaster_type_id,

                # Enum fields
                operation_type=operation_types.get(_key_clean(row[c.OPERATION_TYPE])),
                programme_type=programme_types.get(_key_clean(row[c.PROGRAMME_TYPE])),
                status=statuses.get(_key_clean(row[c.STATUS])),

                name=row[c.PROJECT_NAME],
                start_date=_parse_date(row[c.START_DATE], 'start_date', row_errors),
                end_date=_parse_date(row[c.END_DATE], 'end_date', row_errors),
                budget_amount=_parse_integer(row[c.BUDGET].strip()),

                # Optional fields
                target_male=_parse_integer(row[c.TARGETED_MALES]),
                target_female=_parse_integer(row[c.TARGETED_FEMALES]),
                target_other=_parse_integer(row[c.TARGETED_OTHER]),
                target_total=_parse_integer(row[c.TARGETED_TOTAL]),
                reached_male=_parse_integer(row[c.REACHED_MALES]),
                reached_female=_parse_integer(row[c.REACHED_FEMALES]),
                reached_other=_parse_integer(row[c.REACHED_OTHERS]),
                reached_total=_parse_integer(row[c.REACHED_TOTAL]),
                visibility=visibilities[visibility] if visibility in visibilities else None,
                actual_expenditure=_parse_integer(row[c.ACTUAL_EXPENDITURE]),
                reporting_ns_contact_email=row[c.REPORTING_NS_CONTACT_EMAIL].strip(),
                reporting_ns_contact_name=row[c.REPORTING_NS_CONTACT_NAME].strip(),
                reporting_ns_contact_role=row[c.REPORTING_NS_CONTACT_ROLE].strip(),
                description=row[c.DESCRIPTION].strip(),
            )
            try:
                project.full_clean()
                if len(row_errors) == 0:
                    projects.append([project, project_districts, project_sectortag_ids])
                else:
                    errors.append(_get_error_message(row_number, row_errors))
            except ValidationError as e:
                errors.append(_get_error_message(row_number, row_errors, e.message_dict))

        if len(errors) != 0:
            errors_str = '\n'.join(errors)
            raise Exception(f"Error detected:\n{errors_str}")

        Project.objects.bulk_create([p[0] for p in projects])
        # Set M2M Now
        for project, project_districts, project_sectortag_ids in projects:
            project.project_districts.set(project_districts)
            project.secondary_sectors.set(project_sectortag_ids)
        # Return projects for ProjectImport
        return [p[0] for p in projects]

    def handle_bulk_upload(self, request):
        file = self.cleaned_data['file']
        delimiter = self.cleaned_data['field_delimiter']
        quotechar = self.cleaned_data['string_delimiter']

        try:
            project_import = ProjectImport.objects.none()  # for later reference, if next command fails
            # this should be the first to avoid file.closed state on Azure due to the following command:
            projects = self._handle_bulk_upload(request.user, file, delimiter, quotechar)
            project_import = ProjectImport.objects.create(
                created_by=request.user,
                file=file,
            )
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
        if project_import:
            project_import.save()
