import datetime
import docx

from typing import Any, List

from dref.models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedInterventionIndicators,
    RiskSecurity
)
from api.models import (
    DisasterType,
    Country,
)


def get_text_or_null(colitems: List[Any]):
    if colitems:
        return colitems[0].text
    return None


def parse_boolean_or_null(colitems: List[Any]):
    if colitems:
        return parse_boolean(colitems[0].text)
    return None


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

def parse_int(s):
    try:
        return int(s)
    except ValueError:
        return None


def parse_date(date):
    formats = ['%d/%m/%Y', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date, fmt)
        except ValueError:
            pass
    return None


def parse_disaster_category(disaster_category):
    if disaster_category == 'Yellow':
        disaster_category = Dref.DisasterCategory.YELLOW
    elif disaster_category == 'Orange':
        disaster_category = Dref.DisasterCategory.ORANGE
    elif disaster_category == 'Red':
        disaster_category = Dref.DisasterCategory.RED
    return disaster_category


def parse_disaster_type(disaster_type):
    return DisasterType.objects.filter(name__icontains=disaster_type).first()


def parse_type_of_onset(type):
    if type == 'Slow':
        type = Dref.OnsetType.SLOW
    elif type == 'Sudden':
        type = Dref.OnsetType.SUDDEN
    elif type == 'Imminent':
        type = Dref.OnsetType.IMMINENT
    return type


def parse_string_to_int(string):
    try:
        char_to_check = ','
        if string and char_to_check in string:
            new_strings = string.split(',')
            concat_string = new_strings[0] + new_strings[1]
            return int(concat_string)
        return int(string)
    except ValueError:
        return None


def parse_boolean(string):
    if string and string == 'Yes':
        return True
    elif string and string == 'No':
        return False
    return None

def get_table_data(doc):
    document = docx.Document(doc)
    tables = []
    for table in document.tables:
        rowdata = []
        for r, row in enumerate(table.rows):
            cells = []
            for cell in row.cells:
                cells.append([x.text for x in cell._tc.xpath('.//w:t')])
            rowdata.append(cells)
        tables.append(rowdata)
    return tables


def extract_imminent_file(doc, created_by):
    tables = get_table_data(doc)

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
    document = docx.Document(doc)
    data = {}
    # NOTE: Second Paragraph for Country and Region and Dref Title
    paragraph2 = document.paragraphs[1]
    paragraph_element2 = paragraph2._element.xpath('.//w:t')
    data['title'] = get_text_or_null(paragraph_element2)

    cells = get_table_cells(0)
    data['appeal_code'] = cells(1, 0)
    data['amount_requested'] = parse_string_to_int(cells(1,1,1))
    data['disaster_category'] = parse_disaster_category(cells(1, 2))
    data['disaster_type'] = parse_disaster_type(cells(1,4))
    data['glide_code'] = cells(3, 0)
    data['num_affected'] = parse_string_to_int(cells(3,1))
    data['num_assisted'] = parse_string_to_int(cells(3,2))
    data['type_of_onset'] = parse_type_of_onset(cells(5,0))
    data['date_of_approval'] = parse_date(cells(5,1))
    data['end_date'] = parse_date(cells(5,2))
    data['operation_timeframe'] = parse_int(cells(5,3))
    data['country'] = Country.objects.get(name__icontains=cells(6,0,1))

    paragraph6 = document.paragraphs[7]._element.xpath('.//w:t')
    event_desc = []
    if len(paragraph6) > 0:
        for desc in paragraph6:
            event_desc.append(desc.text)
    data['event_text'] = ''.join(event_desc) if event_desc else None

    paragraph8 = document.paragraphs[9]._element.xpath('.//w:t')
    event_description = []
    if len(paragraph8) > 0:
        for desc in paragraph8:
            event_description.append(desc.text)
    data['event_description'] = ''.join(event_description) if event_description else None
    paragraph11 = document.paragraphs[11]._element.xpath('.//w:t')
    anticipatory_actions_desc = []
    if len(paragraph11) > 0:
        for desc in paragraph11:
            anticipatory_actions_desc.append(desc.text)
    data['anticipatory_actions'] = ''.join(anticipatory_actions_desc) if anticipatory_actions_desc else None
    paragraph13 = document.paragraphs[13]._element.xpath('.//w:t')
    event_scope_description = []
    if len(paragraph13) > 0:
        for desc in paragraph13:
            event_scope_description.append(desc.text)
    data['event_scope'] = ''.join(event_scope_description) if event_scope_description else None

    # Previous Operation
    # NOTE: I am not sure about the index 1 being used below - Bibek
    table1 = document.tables[1]
    cells = get_table_cells(1)

    data['affect_same_area'] = parse_boolean(cells(0,1))
    data['affect_same_population'] = parse_boolean(cells(1,1))
    data['ns_respond'] = parse_boolean(cells(2,1))
    data['ns_request_fund'] = parse_boolean(cells(3, 1))
    data['ns_request_text'] = cells(4,1)
    if cells(4,1) == 'Yes':
        table_one_row_five_column_one = table1.cell(5, 1)._tc.xpath('.//w:t')
        data['dref_recurrent_text'] = get_text_or_null(table_one_row_five_column_one)
    if cells(0,1) == 'Yes' and \
            cells(1, 1) == 'Yes' and \
            cells(2, 1) == 'Yes' and \
            cells(3, 1) == 'Yes' and \
            cells(4, 1) == 'Yes':
        table_one_row_seven_column_one = table1.cell(7, 1)._tc.xpath('.//w:t')
        recurrent_text = []
        if len(table_one_row_seven_column_one) > 0:
            for desc in table_one_row_seven_column_one:
                recurrent_text.append(desc.text)
        data['dref_recurrent_text'] = ''.join(recurrent_text) if recurrent_text else None

    # TODO: uncomment this. was not being used though. This was creating error
    # so has been commented out
    # table_one_row_eight_column_zero = table1.cell(8, 0)._tc.xpath('.//w:t')
    lessons_learned_text = []
    if len(lessons_learned_text) > 0:
        for desc in lessons_learned_text:
            lessons_learned_text.append(desc.text)
    data['lessons_learned'] = ''.join(lessons_learned_text) if lessons_learned_text else None
    # National Socierty Actions
    table2 = document.tables[1]
    cells = get_table_cells(1)
    # National Society
    national_society_actions = []
    column_zero_description = cells(0, 1)
    if column_zero_description:
        data_new = {
            'title': NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS,
            'description': column_zero_description
        }
        national_society_actions.append(data_new)
    column_one_description = cells(1,1)
    if column_one_description:
        data_new = {
            'title': NationalSocietyAction.Title.ASSESSMENT,
            'description': column_one_description
        }
        national_society_actions.append(data_new)
    column_two_description = cells(2, 1)
    if column_two_description:
        data_new = {
            'title': NationalSocietyAction.Title.COORDINATION,
            'description': column_two_description
        }
        national_society_actions.append(data_new)
    column_three_description = cells(3, 1)
    if column_three_description:
        data_new = {
            'title': NationalSocietyAction.Title.RESOURCE_MOBILIZATION,
            'description': column_three_description
        }
        national_society_actions.append(data_new)
    column_four_description = cells(4, 1)
    if column_four_description:
        data_new = {
            'title': NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS,
            'description': column_four_description
        }
        national_society_actions.append(data_new)
    column_five_description = cells(5, 1)
    if column_five_description:
        data_new = {
            'title': NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC,
            'description': column_five_description
        }
        national_society_actions.append(data_new)
    column_six_description = cells(6, 1)
    if column_six_description:
        data_new = {
            'title': NationalSocietyAction.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
            'description': column_six_description
        }
        national_society_actions.append(data_new)
    column_seven_description = cells(7, 1)
    if column_seven_description:
        data_new = {
            'title': NationalSocietyAction.Title.LIVELIHOODS_AND_BASIC_NEEDS,
            'description': column_seven_description
        }
        national_society_actions.append(data_new)
    column_eight_description = cells(8, 1)
    if column_eight_description:
        data_new = {
            'title': NationalSocietyAction.Title.HEALTH,
            'description': column_eight_description
        }
        national_society_actions.append(data_new)
    column_nine_description = cells(9, 1)
    if column_nine_description:
        data_new = {
            'title': NationalSocietyAction.Title.WATER_SANITATION_AND_HYGIENE,
            'description': column_nine_description
        }
        national_society_actions.append(data_new)
    column_ten_description = cells(10, 1)
    if column_ten_description:
        data_new = {
            'title': NationalSocietyAction.Title.PROTECTION_GENDER_AND_INCLUSION,
            'description': column_ten_description
        }
        national_society_actions.append(data_new)
    column_eleven_description = cells(11, 1)
    if column_eleven_description:
        data_new = {
            'title': NationalSocietyAction.Title.EDUCATION,
            'description': column_eleven_description
        }
        national_society_actions.append(data_new)
    column_tweleve_description = cells(12, 1)
    if column_tweleve_description:
        data_new = {
            'title': NationalSocietyAction.Title.MIGRATION,
            'description': column_tweleve_description
        }
        national_society_actions.append(data_new)
    column_thirteen_description = cells(13, 1)
    if column_thirteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
            'description': column_thirteen_description
        }
        national_society_actions.append(data_new)
    column_fourteen_description = cells(14, 1)
    if column_fourteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,
            'description': column_fourteen_description
        }
        national_society_actions.append(data_new)
    column_fifteen_description = cells(15, 1)
    if column_fifteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY,
            'description': column_fifteen_description
        }
        national_society_actions.append(data_new)
    column_sixteen_description = cells(16, 1)
    if column_sixteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.MULTI_PURPOSE_CASH,
            'description': column_sixteen_description
        }
        national_society_actions.append(data_new)
    column_sixteen_description = cells(17, 1)
    if column_sixteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.OTHER,
            'description': column_sixteen_description
        }
        national_society_actions.append(data_new)
    # Crete national Society objects db level
    national_societys = []
    for national_data in national_society_actions:
        national = NationalSocietyAction.objects.create(**national_data)
        national_societys.append(national)

    table3 = document.tables[2]
    cells = get_table_cells(2)
    table_row_zero_column_zero = table3.cell(0 , 1)._tc.xpath('.//w:t')
    ifrc_desc = cells(0, 1, as_list=True) or []

    data['ifrc'] = ''.join(ifrc_desc) if ifrc_desc else None
    table_row_one_column_one = table3.cell(1 , 1)._tc.xpath('.//w:t')
    partner_national_society_desc = cells(1, 1, as_list=True)
    data['partner_national_society'] = ''.join(partner_national_society_desc) if partner_national_society_desc else None

    icrc_desc = cells(2, 1, as_list=True) or []
    data['icrc'] = ''.join(icrc_desc) if icrc_desc else None

    # Other actors
    cells = get_table_cells(3)
    data['government_requested_assistance'] = parse_boolean(cells(0, 1))
    national_authorities = cells(1, 1, as_list=True) or []
    data['national_authorities'] = ''.join(national_authorities) if national_authorities else None

    un_and_other_actors = cells(2, 0, as_list=True) or []
    data['un_or_other_actor'] = ''.join(un_and_other_actors) if un_and_other_actors else None

    coordination_mechanism = cells(3, 1, as_list=True) or []
    data['major_coordination_mechanism'] = ''.join(coordination_mechanism) if coordination_mechanism else None

    # NeedsIdentified
    table5 = document.tables[5]
    cells = get_table_cells(5)
    needs_identified = []
    column_one_description = cells(1, 0)
    if column_one_description:
        data_new = {
            'title': IdentifiedNeed.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
            'description': column_one_description
        }
        needs_identified.append(data_new)
    column_three_description = cells(3, 0)
    if column_three_description:
        data_new = {
            'title': IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
            'description': column_three_description
        }
        needs_identified.append(data_new)
    column_five_description = cells(5, 0)
    if column_five_description:
        data_new = {
            'title': IdentifiedNeed.Title.HEALTH,
            'description': column_five_description
        }
        needs_identified.append(data_new)
    column_seven_description = cells(7, 0)
    if column_seven_description:
        data_new = {
            'title': IdentifiedNeed.Title.WATER_SANITATION_AND_HYGIENE,
            'description': column_seven_description
        }
        needs_identified.append(data_new)
    column_nine_description = cells(9, 0)
    if column_nine_description:
        data_new = {
            'title': IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
            'description': column_nine_description
        }
        needs_identified.append(data_new)
    column_eleven_description = cells(11, 0)
    if column_eleven_description:
        data_new = {
            'title': IdentifiedNeed.Title.EDUCATION,
            'description': column_eleven_description
        }
        needs_identified.append(data_new)
    column_thirteen_description = cells(13, 0)
    if column_thirteen_description:
        data_new = {
            'title': IdentifiedNeed.Title.MIGRATION,
            'description': column_thirteen_description
        }
        needs_identified.append(data_new)
    ## this for community enagagement and accountability
    column_fifteen_description = cells(15, 0)
    if column_fifteen_description:
        data_new = {
            'title': IdentifiedNeed.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
            'description': column_fifteen_description
        }
        needs_identified.append(data_new)
    table_row_sixteen_column_zero = table5.cell(17, 0)._tc.xpath('.//w:t')
    column_sixteen_description = cells(17, 0)
    if column_sixteen_description:
        data_new = {
            'title': IdentifiedNeed.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,
            'description': column_sixteen_description
        }
        needs_identified.append(data_new)
    ## Shelter and Cluster Coordination
    table_row_nineteen_column_zero = table5.cell(19, 0)._tc.xpath('.//w:t')
    column_nineteen_description = get_text_or_null(table_row_nineteen_column_zero)
    if column_nineteen_description:
        data_new = {
            'title': IdentifiedNeed.Title.ENVIRONMENT_SUSTAINABILITY,
            'description': column_nineteen_description
        }
        needs_identified.append(data_new)
    table_row_twentyone_column_zero = table5.cell(21, 0)._tc.xpath('.//w:t')
    column_twentyone_description = table_row_twentyone_column_zero[0].text
    if column_twentyone_description:
        data_new = {
            'title': IdentifiedNeed.Title.SHELTER_CLUSTER_COORDINATION,
            'description': column_twentyone_description
        }
        needs_identified.append(data_new)
    needs = []
    for need in needs_identified:
        identified = IdentifiedNeed.objects.create(**need)
        needs.append(identified)

    operation_objective = document.paragraphs[29]._element.xpath('.//w:t')
    operation_description = []
    if len(operation_objective) > 0:
        for desc in operation_objective:
            operation_description.append(desc.text)
    data['operation_objective'] = ''.join(operation_description) if operation_description else None
    # targeting strategy
    response_strategy = document.paragraphs[31]._element.xpath('.//w:t')
    response_description = []
    if len(response_strategy) > 0:
        for desc in response_strategy:
            response_description.append(desc.text)
    data['response_strategy'] = ''.join(response_description) if response_description else None
    paragraph40 = document.paragraphs[33]._element.xpath('.//w:t')
    people_assisted_description = []
    if len(paragraph40) > 0:
        for desc in paragraph40:
            people_assisted_description.append(desc.text)
    data['people_assisted'] = ''.join(people_assisted_description) if people_assisted_description else None
    paragraph42 = document.paragraphs[35]._element.xpath('.//w:t')
    selection_criteria_description = []
    if len(paragraph42) > 0:
        for desc in paragraph42:
            selection_criteria_description.append(desc.text)
    data['selection_criteria'] = ''.join(selection_criteria_description) if selection_criteria_description else None

    # Targeting Population
    table5 = document.tables[5]
    table_one_row_zero_column_one = table5.cell(0, 1)._tc.xpath('.//w:t')
    data['women'] = parse_string_to_int(table_one_row_zero_column_one[0].text)
    table_one_row_one_column_one = table5.cell(1, 1)._tc.xpath('.//w:t')
    data['girls'] = parse_string_to_int(table_one_row_one_column_one[0].text)
    table_one_row_two_column_one = table5.cell(2, 1)._tc.xpath('.//w:t')
    data['men'] = parse_string_to_int(table_one_row_two_column_one[0].text)
    table_one_row_three_column_one = table5.cell(3, 1)._tc.xpath('.//w:t')
    data['boys'] = parse_string_to_int(table_one_row_three_column_one[0].text)
    table_one_row_four_column_one = table5.cell(4, 1)._tc.xpath('.//w:t')
    data['total_targeted_population'] = parse_string_to_int(table_one_row_four_column_one[0].text)
    table_one_row_one_column_two = table5.cell(1, 2)._tc.xpath('.//w:t')
    data['people_per_local'] = float(table_one_row_one_column_two[0].text)
    table_one_row_one_column_three = table5.cell(1, 3)._tc.xpath('.//w:t')
    data['people_per_urban'] = float(table_one_row_one_column_three[0].text)
    table_one_row_three_column_two = table5.cell(3, 2)._tc.xpath('.//w:t')
    data['disability_people_per'] = float(table_one_row_three_column_two[0].text)
    table_one_row_four_column_three = table5.cell(4, 4)._tc.xpath('.//w:t')
    data['people_targeted_with_early_actions'] = int(table_one_row_four_column_three[0].text)

    # Risk And Security Considerations
    table6 = document.tables[6]
    mitigation_action = []
    table_six_row_two_column_zero = table6.cell(2, 0)._tc.xpath('.//w:t')
    risk = table_six_row_two_column_zero[0].text
    table_six_row_two_column_one = table6.cell(2, 1)._tc.xpath('.//w:t')
    mitigation = table_six_row_two_column_one[0].text
    data_row_one = {
        'risk': risk,
        'mitigation': mitigation,
    }
    mitigation_action.append(data_row_one)
    table_six_row_two_column_zero = table6.cell(3, 0)._tc.xpath('.//w:t')
    risk = table_six_row_two_column_zero[0].text
    table_six_row_two_column_one = table6.cell(3, 1)._tc.xpath('.//w:t')
    mitigation = table_six_row_two_column_one[0].text
    data_row_one = {
        'risk': risk,
        'mitigation': mitigation,
    }
    mitigation_action.append(data_row_one)
    table_six_row_two_column_zero = table6.cell(4, 0)._tc.xpath('.//w:t')
    risk = table_six_row_two_column_zero[0].text
    table_six_row_two_column_one = table6.cell(4, 1)._tc.xpath('.//w:t')
    mitigation = table_six_row_two_column_one[0].text
    data_row_one = {
        'risk': risk,
        'mitigation': mitigation,
    }
    mitigation_action.append(data_row_one)
    mitigation_list = []
    for action in mitigation_action:
        risk_security = RiskSecurity.objects.create(**action)
        mitigation_list.append(risk_security)
    table_six_row_two_column_one = table6.cell(6, 0)._tc.xpath('.//w:t')
    data['risk_security_concern'] = table_six_row_two_column_one[0].text
    # PlannedIntervention Table
    planned_intervention = []
    for i in range(8, 19):
        table = document.tables[i]
        title = table.cell(0, 1)._tc.xpath('.//w:t')[0].text
        budget = table.cell(0, 3)._tc.xpath('.//w:t')[1].text
        targated_population = table.cell(1, 3)._tc.xpath('.//w:t')[0].text

        indicators = []
        title_1 = table.cell(3, 0)._tc.xpath('.//w:t')[0].text
        target_1 = table.cell(3, 2)._tc.xpath('.//w:t')[0].text
        indicator_1 = {
            'title': title_1,
            'target': target_1
        }
        indicators.append(indicator_1)
        title_2 = table.cell(4, 0)._tc.xpath('.//w:t')[0].text
        target_2 = table.cell(4, 2)._tc.xpath('.//w:t')[0].text
        indicator_2 = {
            'title': title_2,
            'target': target_2
        }
        indicators.append(indicator_2)
        title_3 = table.cell(5, 0)._tc.xpath('.//w:t')[0].text
        target_3 = table.cell(5, 2)._tc.xpath('.//w:t')[0].text
        indicator_3 = {
            'title': title_3,
            'target': target_3
        }
        indicators.append(indicator_3)
        indicators_object_list = []
        for indicator in indicators:
            planned_object = PlannedInterventionIndicators.objects.create(**indicator)
            indicators_object_list.append(planned_object)
        description_text = table.cell(6, 1)._tc.xpath('.//w:t')
        priority_description = description_text[0].text
        planned_data = {
            'title': parse_planned_intervention_title(title),
            'budget': budget,
            'person_targeted': targated_population,
            'description': priority_description
        }

        planned = PlannedIntervention.objects.create(**planned_data)
        planned.indicators.add(*indicators_object_list)
        planned_intervention.append(planned)

    # About Support Service
    paragraph66 = document.paragraphs[62]._element.xpath('.//w:t')
    human_resource_description = []
    if len(paragraph66) > 0:
        for desc in paragraph66:
            human_resource_description.append(desc.text)
    data['human_resource'] = ''.join(human_resource_description) if human_resource_description else None
    paragraph68 = document.paragraphs[64]._element.xpath('.//w:t')
    surge_personnel_deployed_description = []
    if len(paragraph68) > 0:
        for desc in paragraph68:
            surge_personnel_deployed_description.append(desc.text)
    data['surge_personnel_deployed'] = ''.join(surge_personnel_deployed_description) if surge_personnel_deployed_description else None
    paragraph70 = document.paragraphs[66]._element.xpath('.//w:t')
    logistic_capacity_of_ns_description = []
    if len(paragraph70) > 0:
        for desc in paragraph70:
            logistic_capacity_of_ns_description.append(desc.text)
    data['logistic_capacity_of_ns'] = ''.join(logistic_capacity_of_ns_description) if logistic_capacity_of_ns_description else None
    paragraph73 = document.paragraphs[69]._element.xpath('.//w:t')
    pmer_description = []
    if len(paragraph73) > 0:
        for desc in paragraph73:
            pmer_description.append(desc.text)
    data['pmer'] = ''.join(pmer_description) if pmer_description else None
    paragraph75 = document.paragraphs[71]._element.xpath('.//w:t')
    communication_description = []
    if len(paragraph75) > 0:
        for desc in paragraph75:
            communication_description.append(desc.text)
    data['communication'] = ''.join(communication_description) if communication_description else None

    # Contact Information
    paragraph80 = document.paragraphs[76]._element.xpath('.//w:t')
    national_society_contact = []
    for paragraph in paragraph80:
        national_society_contact.append(paragraph.text)
    data['national_society_contact_title'] = national_society_contact[3]
    data['national_society_contact_email'] = national_society_contact[5]
    data['national_society_contact_phone_number'] = national_society_contact[7]
    data['national_society_contact_name'] = national_society_contact[0]
    paragraph81 = document.paragraphs[77]._element.xpath('.//w:t')
    ifrc_appeal_manager = []
    for paragraph in paragraph81:
        ifrc_appeal_manager.append(paragraph.text)
    data['ifrc_appeal_manager_title'] = ifrc_appeal_manager[3]
    data['ifrc_appeal_manager_email'] = ifrc_appeal_manager[5]
    data['ifrc_appeal_manager_phone_number'] = ifrc_appeal_manager[7]
    data['ifrc_appeal_manager_name'] = ifrc_appeal_manager[0]
    paragraph82 = document.paragraphs[78]._element.xpath('.//w:t')
    ifrc_project_manager = []
    for paragraph in paragraph82:
        ifrc_project_manager.append(paragraph.text)
    data['ifrc_project_manager_title'] = ifrc_project_manager[3]
    data['ifrc_project_manager_email'] = ifrc_project_manager[5]
    data['ifrc_project_manager_phone_number'] = ifrc_project_manager[7]
    data['ifrc_project_manager_name'] = ifrc_project_manager[0]

    paragraph83 = document.paragraphs[79]._element.xpath('.//w:t')
    ifrc_emergency = []
    for paragraph in paragraph83:
        ifrc_emergency.append(paragraph.text)
    data['ifrc_emergency_title'] = ifrc_emergency[3]
    data['ifrc_emergency_email'] = ifrc_emergency[5]
    data['ifrc_emergency_phone_number'] = ifrc_emergency[7]
    data['ifrc_emergency_name'] = ifrc_emergency[0]

    paragraph84 = document.paragraphs[80]._element.xpath('.//w:t')
    media = []
    for paragraph in paragraph84:
        media.append(paragraph.text)
    data['media_contact_title'] = media[3]
    data['media_contact_email'] = media[5]
    data['media_contact_phone_number'] = media[7]
    data['media_contact_name'] = media[0]

    data['is_published'] = False
    data['national_society'] = Country.objects.get(name_en__icontains=table_row_six_colum_zero[1].text)
    data['created_by'] = created_by
    print(data)
    dref = Dref.objects.create(**data)
    dref.planned_interventions.add(*planned_intervention)
    dref.needs_identified.add(*needs)
    dref.national_society_actions.add(*national_societys)
    dref.risk_security.add(*mitigation_list)
    return dref
