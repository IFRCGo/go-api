import logging

from typing import List, Any

from rest_framework import serializers

from django.conf import settings

from dref.models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedInterventionIndicators,
    RiskSecurity,
)
from api.models import (
    DisasterType,
    Country,
    District
)

from .common_utils import (
    parse_int,
    parse_string_to_int,
    parse_date,
    parse_float,
    parse_boolean,
    get_table_data,
    get_paragraphs_data,
    parse_disaster_category,
    parse_contact_information,
    parse_people,
    parse_country,
    parse_currency,
)


logger = logging.getLogger(__name__)


def parse_national_society_title(title):
    title_dict = {
        'National Society Readiness': NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS,
        'Assessments': NationalSocietyAction.Title.ASSESSMENT,
        'Coordination': NationalSocietyAction.Title.COORDINATION,
        'Resource Mobilization': NationalSocietyAction.Title.RESOURCE_MOBILIZATION,
        'Activation of contingency plans': NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS,
        'EOC': NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC,
        'Shelter, Housing and Settlements': NationalSocietyAction.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        'Livelihoods and Basic Needs': NationalSocietyAction.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        'Health': NationalSocietyAction.Title.HEALTH,
        'Water Sanitation and Hygiene': NationalSocietyAction.Title.WATER_SANITATION_AND_HYGIENE,
        'Protection, Gender and Inclusion': NationalSocietyAction.Title.PROTECTION_GENDER_AND_INCLUSION,
        'Education': NationalSocietyAction.Title.EDUCATION,
        'Migration': NationalSocietyAction.Title.MIGRATION,
        'Risk Reduction, Climate Adaptation and Recovery': NationalSocietyAction.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        'Community Engagement and Accountability': NationalSocietyAction.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,
        'Environment Sustainability': NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY,
        'Multi-purpose Cash': NationalSocietyAction.Title.MULTI_PURPOSE_CASH,
        'Other': NationalSocietyAction.Title.OTHER,

    }
    return title_dict.get(title)


def parse_identified_need_title(title):
    title_dict = {
        'Livelihoods': IdentifiedNeed.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        'Health & Care': IdentifiedNeed.Title.HEALTH,
        'Water, Sanitation and Hygiene (WASH)': IdentifiedNeed.Title.WATER_SANITATION_AND_HYGIENE,
        'Risk Reduction, Climate adaptation and Recovery': IdentifiedNeed.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        'Shelter, Housing and Settlements': IdentifiedNeed.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        'Multi-purpose Cash': IdentifiedNeed.Title.MULTI_PURPOSE_CASH_GRANTS,
        'Protection, Gender, and Inclusion (PGI)': IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
        'Education': IdentifiedNeed.Title.EDUCATION,
        'Migration': IdentifiedNeed.Title.MIGRATION,
        'Environmental Sustainability': IdentifiedNeed.Title.ENVIRONMENT_SUSTAINABILITY,
        'Shelter Cluster Coordination': IdentifiedNeed.Title.SHELTER_CLUSTER_COORDINATION
    }
    return title_dict.get(title)


def parse_planned_intervention_title(title):
    title_dict = {
        'Shelter, Housing and Settlements': PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        'Livelihoods And Basic Needs': PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        'Health': PlannedIntervention.Title.HEALTH,
        'Water, Sanitation And Hygiene': PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE,
        'Protection, Gender And Inclusion': PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION,
        'Education': PlannedIntervention.Title.EDUCATION,
        'Migration': PlannedIntervention.Title.MIGRATION,
        'Risk Reduction, Climate Adaptation And Recovery': PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        'Environmental Sustainability': PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY,
        'Secretariat Services': PlannedIntervention.Title.SECRETARIAT_SERVICES,
        'National Society Strengthening': PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING,
        'Multi-purpose Cash': PlannedIntervention.Title.MULTI_PURPOSE_CASH,
        'Community Engagement and Accountability': PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,


    }
    return title_dict.get(title)


def parse_disaster_type(disaster_type):
    return DisasterType.objects.filter(name__icontains=disaster_type).first()


def parse_type_of_onset(onset_type):
    if onset_type == 'Slow':
        return Dref.OnsetType.SLOW
    elif onset_type == 'Sudden':
        return Dref.OnsetType.SUDDEN
    elif onset_type == 'Imminent':
        return Dref.OnsetType.IMMINENT
    return None


def extract_file(doc, created_by):
    tables = get_table_data(doc)
    paragraphs = get_paragraphs_data(doc)

    data = {}

    # Get item form an array
    def _t(items: List[Any], index=0):
        if items and len(items) > index:
            return items[index]
        return None

    def get_table_cells(table_idx):
        table = tables[table_idx]

        def f(r, c, i=0, as_list=False):
            if as_list:
                return table[r][c]
            return _t(table[r][c], i)
        return f

    # NOTE: Second Paragraph for Country and Region and Dref Title
    title_paragraph = paragraphs[1]
    if len(title_paragraph) > 0:
        data['title'] = title_paragraph[0]
    else:
        raise serializers.ValidationError('Title is required to create dref')

    cells = get_table_cells(0)
    try:
        data['appeal_code'] = cells(1, 0)
    except(IndexError, ValueError):
        pass
    try:
        data['amount_requested'] = parse_currency(cells(1, 1, 1))
    except(IndexError, ValueError):
        pass
    try:
        data['disaster_category'] = parse_disaster_category(cells(1, 2))
    except(IndexError, ValueError):
        pass
    try:
        data['disaster_type'] = parse_disaster_type(cells(1, 4))
    except(IndexError, ValueError):
        pass
    try:
        data['glide_code'] = cells(3, 0)
    except(IndexError, ValueError):
        pass
    try:
        data['num_affected'] = parse_people(cells(3, 1))
    except(IndexError, ValueError):
        pass
    try:
        data['num_assisted'] = parse_people(cells(3, 2))
    except(IndexError, ValueError):
        pass
    try:
        data['type_of_onset'] = parse_type_of_onset(cells(5, 0))
    except(IndexError, ValueError):
        pass
    try:
        data['date_of_approval'] = parse_date(cells(5, 1))
    except(IndexError, ValueError):
        pass
    try:
        data['end_date'] = parse_date(cells(5, 2))
    except(IndexError, ValueError):
        pass
    try:
        data['operation_timeframe'] = parse_people(cells(5, 3))
    except(IndexError, ValueError):
        pass
    country = Country.objects.filter(name__icontains=parse_country(cells(6, 0))).first()
    if country is None:
        raise serializers.ValidationError('A valid country name is required')
    data['country'] = country
    district = cells(6, 2)
    new_district = district.split(',')
    district_list = []
    for d in new_district:
        try:
            district = District.objects.filter(
                country__name__icontains=parse_country(cells(6, 0)),
                name__icontains=d
            ).first()
        except District.DoesNotExist:
            pass
        if district is None:
            continue
        district_list.append(district)

    try:
        description = paragraphs[7]
        data['event_description'] = ''.join(description) if description else None
    except (IndexError, ValueError):
        pass
    try:
        event_scope = paragraphs[9]
        data['event_scope'] = ''.join(event_scope) if event_scope else None
    except(IndexError, ValueError):
        pass

    # Previous Operation
    cells = get_table_cells(1)
    try:
        data['affect_same_area'] = parse_boolean(cells(0, 1))
    except(IndexError, ValueError):
        pass
    try:
        data['affect_same_population'] = parse_boolean(cells(1, 1))
    except(IndexError, ValueError):
        pass
    try:
        data['ns_respond'] = parse_boolean(cells(2, 1))
    except(IndexError, ValueError):
        pass
    try:
        data['ns_request_fund'] = parse_boolean(cells(3, 1))
    except(IndexError, ValueError):
        pass
    try:
        data['ns_request_text'] = cells(4, 1)
        if cells(4, 1) == 'Yes':
            data['dref_recurrent_text'] = cells(5, 1)
    except(IndexError, ValueError):
        pass
    try:
        if cells(0, 1) == 'Yes' and cells(1, 1) == 'Yes' and cells(2, 1) == 'Yes' and cells(3, 1) == 'Yes' and cells(4, 1) == 'Yes':
            recurrent_text = cells(7, 1, as_list=True) or []
            data['dref_recurrent_text'] = ''.join(recurrent_text) if recurrent_text else None
    except(IndexError, ValueError):
        pass
    try:
        data['lessons_learned'] = cells(8, 1)
    except IndexError:
        pass
    ## Movement Parameters
    cells = get_table_cells(3)
    try:
        ifrc_desc = cells(0, 1, as_list=True) or []
        data['ifrc'] = ''.join(ifrc_desc) if ifrc_desc else None
        partner_national_society_desc = cells(1, 1, as_list=True) or []
        data['partner_national_society'] = ''.join(partner_national_society_desc) if partner_national_society_desc else None
        icrc_desc = cells(2, 1, as_list=True) or []
        data['icrc'] = ''.join(icrc_desc) if icrc_desc else None
    except IndexError:
        pass

    # National Society Actions
    action_titles = [
        NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS,
        NationalSocietyAction.Title.ASSESSMENT,
        NationalSocietyAction.Title.COORDINATION,
        NationalSocietyAction.Title.RESOURCE_MOBILIZATION,
        NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS,
        NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC,
        NationalSocietyAction.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        NationalSocietyAction.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        NationalSocietyAction.Title.HEALTH,
        NationalSocietyAction.Title.WATER_SANITATION_AND_HYGIENE,
        NationalSocietyAction.Title.PROTECTION_GENDER_AND_INCLUSION,
        NationalSocietyAction.Title.EDUCATION,
        NationalSocietyAction.Title.MIGRATION,
        NationalSocietyAction.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        NationalSocietyAction.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,
        NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY,
        NationalSocietyAction.Title.MULTI_PURPOSE_CASH,
        NationalSocietyAction.Title.OTHER,
    ]

    cells = get_table_cells(2)
    # National Society
    national_society_actions = []
    for i, title in enumerate(action_titles):
        try:
            description = cells(i, 1)
            if description:
                data_new = {
                    'title': title,
                    'description': description,
                }
                national_society_actions.append(data_new)
        except IndexError:
            pass

    # Crete national Society objects db level
    national_societies = []
    for national_data in national_society_actions:
        if national_data['description']:
            national = NationalSocietyAction.objects.create(**national_data)
            national_societies.append(national)
    # Other actors
    cells = get_table_cells(4)
    try:
        if cells(0, 0):
            data['government_requested_assistance'] = parse_boolean(cells(0, 1))
    except (ValueError, IndexError):
        pass
    try:
        national_authorities = cells(1, 2, as_list=True) or []
        data['national_authorities'] = ''.join(national_authorities) if national_authorities else None
    except (ValueError, IndexError):
        pass

    try:
        un_and_other_actors = cells(2, 2, as_list=True) or []
        data['un_or_other_actor'] = ''.join(un_and_other_actors) if un_and_other_actors else None
    except (IndexError, ValueError):
        pass

    try:
        coordination_mechanism = cells(4, 0, as_list=True) or []
        data['major_coordination_mechanism'] = ''.join(coordination_mechanism) if coordination_mechanism else None
    except (IndexError, ValueError):
        pass
    # NeedsIdentified
    cells = get_table_cells(5)
    needs_identified = []
    needs_titles = [
        IdentifiedNeed.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
        IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
        IdentifiedNeed.Title.HEALTH,
        IdentifiedNeed.Title.WATER_SANITATION_AND_HYGIENE,
        IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
        IdentifiedNeed.Title.EDUCATION,
        IdentifiedNeed.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        IdentifiedNeed.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,
        IdentifiedNeed.Title.ENVIRONMENT_SUSTAINABILITY,
        IdentifiedNeed.Title.SHELTER_CLUSTER_COORDINATION,
    ]
    for i, needs_title in enumerate(needs_titles):
        try:
            description = cells(i * 2 + 1, 0)  # Use Every alternate row, so i*2 + 1
            if description:
                data_new = {
                    'title': needs_title,
                    'description': description
                }
                needs_identified.append(data_new)
        except IndexError:
            pass

    needs = []
    for need in needs_identified:
        if need['description']:
            identified = IdentifiedNeed.objects.create(**need)
            needs.append(identified)
    try:
        if paragraphs[23][0] == 'Overall objective of the operation':
            try:
                data['operation_objective'] = ''.join(paragraphs[24] or [])
            except (IndexError, ValueError):
                pass
    except IndexError:
        pass

    # targeting strategy
    try:
        if paragraphs[26][0] == 'Response strategy rationale':
            try:
                data['response_strategy'] = ''.join(paragraphs[27] or [])
            except (IndexError, ValueError):
                pass
    except IndexError:
        pass
    try:
        if paragraphs[30][0] == 'Who will be targeted through this operation?':
            try:
                data['people_assisted'] = ''.join(paragraphs[31] or [])
            except(IndexError, ValueError):
                pass
    except IndexError:
        pass
    try:
        if paragraphs[33][0] == 'Explain the selection criteria for the targeted population':
            try:
                data['selection_criteria'] = ''.join(paragraphs[34] or [])
            except(IndexError, ValueError):
                pass
    except IndexError:
        pass

    # Targeting Population
    cells = get_table_cells(6)
    categories = ['women', 'girls', 'men', 'boys', 'total_targeted_population']
    for i, category in enumerate(categories):
        try:
            data[category] = parse_string_to_int(cells(i, 1))
        except(IndexError, ValueError):
            pass

    try:
        data['people_per_local'] = parse_float(cells(1, 2))
    except(IndexError, ValueError):
        pass
    try:
        data['people_per_urban'] = parse_float(cells(1, 3))
    except(IndexError, ValueError):
        pass
    try:
        data['disability_people_per'] = parse_float(cells(3, 2))
    except(IndexError, ValueError):
        pass

    # Risk And Security Considerations
    cells = get_table_cells(7)
    mitigation_actions_rows = range(2, 5)
    mitigation_actions = []
    for i in mitigation_actions_rows:
        try:
            data_row_one = {
                'risk': cells(i, 0),
                'mitigation': cells(i, 1),
            }
            mitigation_actions.append(data_row_one)
        except(IndexError, ValueError):
            pass

    try:
        data['risk_security_concern'] = cells(6, 0)
    except IndexError:
        pass

    risk_security_list = []
    for mitigation in mitigation_actions:
        if mitigation['risk'] or mitigation['mitigation']:
            risk_security = RiskSecurity.objects.create(**mitigation)
            risk_security_list.append(risk_security)

    # About Support Service
    try:
        if paragraphs[57][0] == 'How many volunteers and staff involved in the response? Briefly describe their role.':
            data['human_resource'] = ''.join(paragraphs[58] or [])
    except (IndexError, ValueError):
        pass
    try:
        if paragraphs[59][0] == 'Will surge personnel be deployed? Please provide the role profile needed.':
            data['surge_personnel_deployed'] = ''.join(paragraphs[60] or [])
            if data['surge_personnel_deployed']:
                data['is_surge_personnel_deployed'] = True
    except (IndexError, ValueError):
        pass
    try:
        if paragraphs[61][0] == 'If there is procurement, will it be done by National Society or IFRC?':
            data['logistic_capacity_of_ns'] = ''.join(paragraphs[62] or [])
    except (IndexError, ValueError):
        pass
    try:
        if paragraphs[65][0] == 'How will this operation be monitored?':
            data['pmer'] = ''.join(paragraphs[66] or [])
    except (IndexError, ValueError):
        pass
    try:
        if paragraphs[67][0] == 'Please briefly explain the National Societies communication strategy for this operation.':
            data['communication'] = ''.join(paragraphs[68] or [])
    except (IndexError, ValueError):
        pass

    try:
        national_society_contact = parse_contact_information(paragraphs[72] or [])
        data['national_society_contact_title'] = national_society_contact[2] if national_society_contact[2] and national_society_contact[2] != ", , " else None
        data['national_society_contact_email'] = national_society_contact[4] if national_society_contact[4] else None
        data['national_society_contact_phone_number'] = national_society_contact[6] if national_society_contact[6] else None
        data['national_society_contact_name'] = national_society_contact[0] if national_society_contact[0] else None
    except IndexError:
        pass
    try:

        ifrc_appeal_manager = parse_contact_information(paragraphs[73] or [])
        data['ifrc_appeal_manager_title'] = ifrc_appeal_manager[2] if ifrc_appeal_manager[2] else None
        data['ifrc_appeal_manager_email'] = ifrc_appeal_manager[4] if ifrc_appeal_manager[4] else None
        data['ifrc_appeal_manager_phone_number'] = ifrc_appeal_manager[6] if ifrc_appeal_manager[6] else None
        data['ifrc_appeal_manager_name'] = ifrc_appeal_manager[0] if ifrc_appeal_manager[0] else None
    except IndexError:
        pass

    try:
        ifrc_project_manager = parse_contact_information(paragraphs[74] or [])
        data['ifrc_project_manager_title'] = ifrc_project_manager[2] if ifrc_project_manager[2] else None
        data['ifrc_project_manager_email'] = ifrc_project_manager[4] if ifrc_project_manager[4] else None
        data['ifrc_project_manager_phone_number'] = ifrc_project_manager[6] if ifrc_project_manager[6] else None
        data['ifrc_project_manager_name'] = ifrc_project_manager[0] if ifrc_project_manager[0] else None
    except IndexError:
        pass

    try:
        ifrc_emergency = parse_contact_information(paragraphs[75] or [])
        data['ifrc_emergency_title'] = ifrc_emergency[2] if ifrc_emergency[2] else None
        data['ifrc_emergency_email'] = ifrc_emergency[4] if ifrc_emergency[4] else None
        data['ifrc_emergency_phone_number'] = ifrc_emergency[6] if ifrc_emergency[6] else None
        data['ifrc_emergency_name'] = ifrc_emergency[0] if ifrc_emergency[0] else None
    except IndexError:
        pass

    try:
        media = parse_contact_information(paragraphs[76] or [])
        data['media_contact_title'] = media[2] if media[2] else None
        data['media_contact_email'] = media[4] if media[4] else None
        data['media_contact_phone_number'] = media[6] if media[6] else None
        data['media_contact_name'] = media[0] if media[0] else None
    except IndexError:
        pass

    # PlannedIntervention Table
    planned_intervention = []
    for i in range(8, 19):
        cells = get_table_cells(i)
        title = cells(0, 1)
        budget = cells(0, 3, 1)
        targeted_population = cells(1, 3)

        indicators = []
        for j in range(3, 6):
            try:
                indicators.append({
                    'title': cells(j, 0),
                    'target': parse_int(cells(j, 2)),
                })
            except(IndexError, ValueError):
                pass

        indicators_object_list = []
        for indicator in indicators:
            if indicator['title']:
                planned_object = PlannedInterventionIndicators.objects.create(**indicator)
                indicators_object_list.append(planned_object)

        priority_description = cells(6, 1)
        planned_data = {
            'title': parse_planned_intervention_title(title),
            'budget': parse_int(budget),
            'person_targeted': parse_int(targeted_population),
            'description': priority_description
        }
        if planned_data['budget'] or planned_data['person_targeted'] or planned_data['description']:
            planned = PlannedIntervention.objects.create(**planned_data)
            planned.indicators.add(*indicators_object_list)
            planned_intervention.append(planned)

    # Create dref objects
    # map m2m fields
    data['is_published'] = False
    data['national_society'] = country
    data['created_by'] = created_by
    dref = Dref.objects.create(**data)
    dref.planned_interventions.add(*planned_intervention)
    dref.needs_identified.add(*needs)
    dref.national_society_actions.add(*national_societies)
    dref.risk_security.add(*risk_security_list)
    if len(district_list) > 0 and None not in district_list:
        dref.district.add(*district_list)
    return dref


def get_email_context(instance):
    from dref.serializers import DrefSerializer

    dref_data = DrefSerializer(instance).data
    email_context = {
        'id': dref_data['id'],
        'title': dref_data['title'],
        'frontend_url': settings.FRONTEND_URL,
    }
    return email_context
