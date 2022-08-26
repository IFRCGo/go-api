import datetime
import docx

from dref.models import (
    Dref,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
    PlannedInterventionIndicators,
)
from api.models import (
    DisasterType,
    Country,
)


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


def is_valid_date(date):
    try:
        return datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
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
        type = Dref.OnsetType.Imminent
    return type


def parse_string_to_int(string):
    char_to_check = ','
    if string and char_to_check in string:
        new_strings = string.split(',')
        concat_string = new_strings[0] + new_strings[1]
        return int(concat_string)
    return int(string)


def parse_boolean(string):
    if string and string == 'Yes':
        return True
    elif string and string == 'No':
        return False
    return None


def extract_file(doc, created_by):
    document = docx.Document(doc)
    data = {}
    # NOTE: Second Paragraph for Country and Region and Dref Title
    paragraph2 = document.paragraphs[1]
    paragraph_element2 = paragraph2._element.xpath('.//w:t')
    data['title'] = paragraph_element2[0].text
    table = document.tables[0]
    table_row_one_column_zero = table.cell(1 , 0)._tc.xpath('.//w:t')
    data['appeal_code'] = table_row_one_column_zero[0].text
    table_row_one_column_one = table.cell(1, 1)._tc.xml
    data['amount_requested'] = parse_string_to_int(table_row_one_column_one[1].text)
    table_row_one_colum_two = table.cell(1, 2)._tc.xpath('.//w:t')
    data['disaster_category'] = parse_disaster_category(table_row_one_colum_two[0].text)
    table_row_one_column_four = table.cell(1, 4)._tc.xpath('.//w:t')
    data['disaster_type'] = parse_disaster_type(table_row_one_column_four[0].text)
    table_row_three_column_one = table.cell(3, 0)._tc.xpath('.//w:t')
    data['glide_code'] = table_row_three_column_one[0].text
    table_row_three_column_one = table.cell(3, 1)._tc.xpath('.//w:t')
    data['num_affected'] = parse_string_to_int(table_row_three_column_one[0].text)
    table_row_three_column_two = table.cell(3, 2)._tc.xpath('.//w:t')
    data['num_assisted'] = parse_string_to_int(table_row_three_column_two[0].text)
    table_row_five_column_zero = table.cell(5, 0)._tc.xpath('.//w:t')
    data['type_of_onset'] = parse_type_of_onset(table_row_five_column_zero[0].text)
    table_row_five_column_one = table.cell(5, 1)._tc.xpath('.//w:t')
    data['date_of_approval'] = is_valid_date(table_row_five_column_one[0].text)
    table_row_five_column_two = table.cell(5, 2)._tc.xpath('.//w:t')
    data['end_date'] = is_valid_date(table_row_five_column_two[0].text)
    table_row_five_colum_three = table.cell(5, 3)._tc.xpath('.//w:t')
    data['operation_timeframe'] = int(table_row_five_colum_three[0].text)
    table_row_six_colum_zero = table.cell(6, 0)._tc.xml
    data['country'] = Country.objects.filter(name__icontains=table_row_six_colum_zero[0].text)
    paragraph7 = document.paragraphs[7]
    paragraph_element7 = paragraph7._element.xpath('.//w:t')
    description = []
    if len(paragraph_element7) > 0:
        for desc in paragraph_element7:
            description.append(desc.text)
    data['event_description'] = ''.join(description) if description else None
    paragraph13 = document.paragraphs[13]
    paragraph_element13 = paragraph13._element.xpath('.//w:t')
    event_scope = []
    if len(paragraph_element13) > 0:
        for desc in paragraph_element13:
            event_scope.append(desc.text)
    data['event_scope'] = ''.join(event_scope) if event_scope else None
    # Previous Operation
    table1 = document.tables[1]
    table_one_row_zero_column_one = table1.cell(0, 1)._tc.xpath('.//w:t')
    data['affect_same_area'] = parse_boolean(table_one_row_zero_column_one[0].text)
    table_one_row_one_column_one = table1.cell(1, 1)._tc.xpath('.//w:t')
    data['affect_same_population'] = parse_boolean(table_one_row_one_column_one[0].text)
    table_one_row_two_column_one = table1.cell(2, 1)._tc.xpath('.//w:t')
    data['ns_respond'] = parse_boolean(table_one_row_two_column_one[0].text)
    table_one_row_three_column_one = table1.cell(3, 1)._tc.xpath('.//w:t')
    data['ns_request_fund'] = parse_boolean(table_one_row_three_column_one[0].text)
    table_one_row_four_column_one = table1.cell(4, 1)._tc.xpath('.//w:t')
    data['ns_request_text'] = table_one_row_four_column_one[0].text
    if table_one_row_four_column_one == 'Yes':
        table_one_row_five_column_one = table1.cell(5, 1)._tc.xpath('.//w:t')
        data['dref_recurrent_text'] = table_one_row_five_column_one[0].text
    if table_one_row_zero_column_one == 'Yes' and table_one_row_one_column_one == 'Yes' and table_one_row_two_column_one == 'Yes' and table_one_row_three_column_one == 'Yes' and table_one_row_four_column_one == 'Yes':
        table_one_row_seven_column_one = table1.cell(7, 1)._tc.xpath('.//w:t')
        recurrent_text = []
        if len(table_one_row_seven_column_one) > 0:
            for desc in table_one_row_seven_column_one:
                recurrent_text.append(desc.text)
        data['dref_recurrent_text'] = ''.join(recurrent_text) if recurrent_text else None
    table_one_row_eight_column_zero = table1.cell(8, 0)._tc.xpath('//w:t')
    data['lessons_learned'] = table_one_row_eight_column_zero[0].text

    ## Movement Parameters
    table3 = document.tables[3]
    table_row_zero_column_zero = table3.cell(0 , 1)._tc.xpath('.//w:t')
    ifrc_desc = []
    if len(table_row_zero_column_zero) > 0:
        for desc in table_row_zero_column_zero:
            ifrc_desc.append(desc.text)
    data['ifrc'] = ''.join(ifrc_desc) if ifrc_desc else None
    table_row_one_column_one = table3.cell(1 , 1)._tc.xpath('.//w:t')
    partner_national_society_desc = []
    if len(table_row_one_column_one) > 0:
        for desc in table_row_one_column_one:
            partner_national_society_desc.append(desc.text)
    data['partner_national_society'] = ''.join(partner_national_society_desc) if partner_national_society_desc else None
    table_row_two_column_two = table3.cell(2, 1)._tc.xpath('.//w:t')
    icrc_desc = []
    if len(table_row_two_column_two) > 0:
        for desc in table_row_two_column_two:
            icrc_desc.append(desc.text)
    data['icrc'] = ''.join(icrc_desc) if icrc_desc else None

    # National Socierty Actions
    table2 = document.tables[2]
    # National Society
    national_society_actions = []
    table_row_zero_column_one = table2.cell(0, 1)._tc.xpath('.//w:t')
    column_zero_description = table_row_zero_column_one[0].text
    if column_zero_description:
        data_new = {
            'title': NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS,
            'description': column_zero_description
        }
        national_society_actions.append(data_new)
    table_row_one_column_one = table2.cell(1, 1)._tc.xpath('.//w:t')
    column_one_description = table_row_one_column_one[0].text
    if column_one_description:
        data_new = {
            'title': NationalSocietyAction.Title.ASSESSMENT,
            'description': column_one_description
        }
        national_society_actions.append(data_new)
    table_row_two_column_one = table2.cell(2, 1)._tc.xpath('.//w:t')
    column_two_description = table_row_two_column_one[0].text
    if column_two_description:
        data_new = {
            'title': NationalSocietyAction.Title.COORDINATION,
            'description': column_two_description
        }
        national_society_actions.append(data_new)
    table_row_three_column_one = table2.cell(3, 1)._tc.xpath('.//w:t')
    column_three_description = table_row_three_column_one[0].text
    if column_three_description:
        data_new = {
            'title': NationalSocietyAction.Title.RESOURCE_MOBILIZATION,
            'description': column_three_description
        }
        national_society_actions.append(data_new)
    table_row_four_column_one = table2.cell(4, 1)._tc.xpath('.//w:t')
    column_four_description = table_row_four_column_one[0].text
    if column_four_description:
        data_new = {
            'title': NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS,
            'description': column_four_description
        }
        national_society_actions.append(data_new)
    table_row_five_column_one = table2.cell(5, 1)._tc.xpath('.//w:t')
    column_five_description = table_row_five_column_one[0].text
    if column_five_description:
        data_new = {
            'title': NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC,
            'description': column_five_description
        }
        national_society_actions.append(data_new)
    table_row_six_column_one = table2.cell(6, 1)._tc.xpath('.//w:t')
    column_six_description = table_row_six_column_one[0].text
    if column_six_description:
        data_new = {
            'title': NationalSocietyAction.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
            'description': column_six_description
        }
        national_society_actions.append(data_new)
    table_row_seven_column_one = table2.cell(7, 1)._tc.xpath('.//w:t')
    column_seven_description = table_row_seven_column_one[0].text
    if column_seven_description:
        data_new = {
            'title': NationalSocietyAction.Title.LIVELIHOODS_AND_BASIC_NEEDS,
            'description': column_seven_description
        }
        national_society_actions.append(data_new)
    table_row_eight_column_one = table2.cell(8, 1)._tc.xpath('.//w:t')
    column_eight_description = table_row_eight_column_one[0].text
    if column_eight_description:
        data_new = {
            'title': NationalSocietyAction.Title.HEALTH,
            'description': column_eight_description
        }
        national_society_actions.append(data_new)
    table_row_nine_column_one = table2.cell(9, 1)._tc.xpath('.//w:t')
    column_nine_description = table_row_nine_column_one[0].text
    if column_nine_description:
        data_new = {
            'title': NationalSocietyAction.Title.WATER_SANITATION_AND_HYGIENE,
            'description': column_nine_description
        }
        national_society_actions.append(data_new)
    table_row_ten_column_one = table2.cell(10, 1)._tc.xpath('.//w:t')
    column_ten_description = table_row_ten_column_one[0].text
    if column_ten_description:
        data_new = {
            'title': NationalSocietyAction.Title.PROTECTION_GENDER_AND_INCLUSION,
            'description': column_ten_description
        }
        national_society_actions.append(data_new)
    table_row_eleven_column_one = table2.cell(11, 1)._tc.xpath('.//w:t')
    column_eleven_description = table_row_eleven_column_one[0].text
    if column_eleven_description:
        data_new = {
            'title': NationalSocietyAction.Title.EDUCATION,
            'description': column_eleven_description
        }
        national_society_actions.append(data_new)
    table_row_tweleve_column_one = table2.cell(12, 1)._tc.xpath('.//w:t')
    column_tweleve_description = table_row_tweleve_column_one[0].text
    if column_tweleve_description:
        data_new = {
            'title': NationalSocietyAction.Title.MIGRATION,
            'description': column_tweleve_description
        }
        national_society_actions.append(data_new)
    table_row_thirteen_column_one = table2.cell(13, 1)._tc.xpath('.//w:t')
    column_thirteen_description = table_row_thirteen_column_one[0].text
    if column_thirteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
            'description': column_thirteen_description
        }
        national_society_actions.append(data_new)
    table_row_fourteen_column_one = table2.cell(14, 1)._tc.xpath('.//w:t')
    column_fourteen_description = table_row_fourteen_column_one[0].text
    if column_fourteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,
            'description': column_fourteen_description
        }
        national_society_actions.append(data_new)
    table_row_fifteen_column_one = table2.cell(15, 1)._tc.xpath('.//w:t')
    column_fifteen_description = table_row_fifteen_column_one[0].text
    if column_fifteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY,
            'description': column_fifteen_description
        }
        national_society_actions.append(data_new)
    table_row_sixteen_column_one = table2.cell(16, 1)._tc.xpath('.//w:t')
    column_sixteen_description = table_row_sixteen_column_one[0].text
    if column_sixteen_description:
        data_new = {
            'title': NationalSocietyAction.Title.ENVIRONMENT_SUSTAINABILITY,
            'description': column_sixteen_description
        }
        national_society_actions.append(data_new)
    # Crete national Society objects db level
    national_societys = []
    for national_data in national_society_actions:
        national = NationalSocietyAction.objects.create(**national_data)
        national_societys.append(national)
    # Other actors
    table4 = document.tables[4]
    table_row_zero_column_one = table4.cell(0 , 1)._tc.xpath('.//w:t')
    if len(table_row_zero_column_zero) > 0:
        data['government_requested_assistance'] = parse_boolean(table_row_zero_column_one[0].text)
    table_row_one_column_one = table4.cell(1 , 1)._tc.xpath('.//w:t')
    national_authorities = []
    if len(table_row_one_column_one) > 0:
        for authorities in table_row_one_column_one:
            national_authorities.append(authorities.text)
    data['national_authorities'] = ''.join(national_authorities) if national_authorities else None
    un_and_other_actors = []
    table_row_two_column_one = table4.cell(2 , 1)._tc.xpath('.//w:t')
    if len(table_row_two_column_one) > 0:
        for authorities in table_row_two_column_one:
            un_and_other_actors.append(authorities.text)
    data['un_or_other_actor'] = ''.join(un_and_other_actors) if un_and_other_actors else None
    coordination_mechanism = []
    table_row_three_column_one = table4.cell(3, 1)._tc.xpath('.//w:t')
    if len(table_row_three_column_one) > 0:
        for coordination in table_row_three_column_one:
            coordination_mechanism.append(coordination.text)
    data['major_coordination_mechanism'] = ''.join(coordination_mechanism) if coordination_mechanism else None
    # NeedsIdentified
    table5 = document.tables[5]
    needs_identified = []
    table_row_one_column_zero = table5.cell(1, 0)._tc.xpath('.//w:t')
    column_one_description = table_row_one_column_zero[0].text
    if column_one_description:
        data_new = {
            'title': IdentifiedNeed.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
            'description': column_one_description
        }
        needs_identified.append(data_new)
    table_row_three_column_zero = table5.cell(3, 0)._tc.xpath('.//w:t')
    column_three_description = table_row_three_column_zero[0].text
    if column_three_description:
        data_new = {
            'title': IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
            'description': column_three_description
        }
        needs_identified.append(data_new)
    table_row_five_column_zero = table5.cell(5, 0)._tc.xpath('.//w:t')
    column_five_description = table_row_five_column_zero[0].text
    if column_five_description:
        data_new = {
            'title': IdentifiedNeed.Title.HEALTH,
            'description': column_five_description
        }
        needs_identified.append(data_new)
    table_row_seven_column_zero = table5.cell(7, 0)._tc.xpath('.//w:t')
    column_seven_description = table_row_seven_column_zero[0].text
    if column_seven_description:
        data_new = {
            'title': IdentifiedNeed.Title.WATER_SANITATION_AND_HYGIENE,
            'description': column_seven_description
        }
        needs_identified.append(data_new)
    table_row_nine_column_zero = table5.cell(9, 0)._tc.xpath('.//w:t')
    column_nine_description = table_row_nine_column_zero[0].text
    if column_nine_description:
        data_new = {
            'title': IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
            'description': column_nine_description
        }
        needs_identified.append(data_new)
    table_row_eleven_column_zero = table5.cell(11, 0)._tc.xpath('.//w:t')
    column_eleven_description = table_row_eleven_column_zero[0].text
    if column_eleven_description:
        data_new = {
            'title': IdentifiedNeed.Title.EDUCATION,
            'description': column_eleven_description
        }
        needs_identified.append(data_new)
    table_row_thirteen_column_zero = table5.cell(13, 0)._tc.xpath('.//w:t')
    column_thirteen_description = table_row_thirteen_column_zero[0].text
    if column_thirteen_description:
        data_new = {
            'title': IdentifiedNeed.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
            'description': column_thirteen_description
        }
        needs_identified.append(data_new)
    ## this for community enagagement and accountability
    table_row_fifteen_column_zero = table5.cell(15, 0)._tc.xpath('.//w:t')
    column_fifteen_description = table_row_fifteen_column_zero[0].text
    if column_fifteen_description:
        data_new = {
            'title': IdentifiedNeed.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
            'description': column_fifteen_description
        }
        needs_identified.append(data_new)
    table_row_sixteen_column_zero = table5.cell(17, 0)._tc.xpath('.//w:t')
    column_sixteen_description = table_row_sixteen_column_zero[0].text
    if column_sixteen_description:
        data_new = {
            'title': IdentifiedNeed.Title.ENVIRONMENT_SUSTAINABILITY,
            'description': column_sixteen_description
        }
        needs_identified.append(data_new)
    ## Shelter and Cluster Coordination
    table_row_nineteen_column_zero = table5.cell(19, 0)._tc.xpath('.//w:t')
    column_nineteen_description = table_row_nineteen_column_zero[0].text
    if column_nineteen_description:
        data_new = {
            'title': IdentifiedNeed.Title.SHELTER_HOUSING_AND_SETTLEMENTS,
            'description': column_nineteen_description
        }
        needs_identified.append(data_new)
    needs = []
    for need in needs_identified:
        identified = IdentifiedNeed.objects.create(**need)
        needs.append(identified)
    operation_objective = document.paragraphs[27]._element.xpath('.//w:t')
    data['operation_objective'] = operation_objective[0].text if operation_objective else None
    # targeting strategy
    paragraph30 = document.paragraphs[30]._element.xpath('.//w:t')
    data['response_strategy'] = paragraph30[0].text if len(paragraph30) > 0 else None
    paragraph34 = document.paragraphs[34]._element.xpath('.//w:t')
    data['people_assisted'] = paragraph34[0].text if len(paragraph34) > 0 else None
    paragraph36 = document.paragraphs[36]._element.xpath('.//w:t')
    data['selection_criteria'] = paragraph36[0].text if len(paragraph36) > 0 else None

    # Targeting Population
    table5 = document.tables[6]
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

    # Risk And Security Considerations
    table6 = document.tables[7]
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
    table_six_row_two_column_one = table6.cell(6, 0)._tc.xpath('.//w:t')
    data['risk_security_concern'] = table_six_row_two_column_one[0].text

    # Planned Intervention
    table7 = document.tables[8]
    # About Support Service
    paragraph58 = document.paragraphs[58]._element.xpath('.//w:t')
    data['human_resource'] = paragraph58[0].text
    paragraph60 = document.paragraphs[60]._element.xpath('.//w:t')
    data['surge_personnel_deployed'] = paragraph60[0].text
    paragraph62 = document.paragraphs[62]._element.xpath('.//w:t')
    data['logistic_capacity_of_ns'] = paragraph62[0].text
    paragraph64 = document.paragraphs[64]._element.xpath('.//w:t')
    data['pmer'] = paragraph64[0].text
    paragraph66 = document.paragraphs[66]._element.xpath('.//w:t')
    data['communication'] = paragraph66[0].text
    paragraph72 = document.paragraphs[72]._element.xpath('.//w:t')
    national_society_contact = []
    for paragraph in paragraph72:
        national_society_contact.append(paragraph.text)
    data['national_society_contact_title'] = national_society_contact[3]
    data['national_society_contact_email'] = national_society_contact[5]
    data['national_society_contact_phone_number'] = national_society_contact[7]
    data['national_society_contact_name'] = national_society_contact[0]
    paragraph73 = document.paragraphs[73]._element.xpath('.//w:t')
    ifrc_appeal_manager = []
    for paragraph in paragraph73:
        ifrc_appeal_manager.append(paragraph.text)
    data['ifrc_appeal_manager_title'] = ifrc_appeal_manager[3]
    data['ifrc_appeal_manager_email'] = ifrc_appeal_manager[5]
    data['ifrc_appeal_manager_phone_number'] = ifrc_appeal_manager[7]
    data['ifrc_appeal_manager_name'] = ifrc_appeal_manager[0]
    paragraph74 = document.paragraphs[74]._element.xpath('.//w:t')
    ifrc_project_manager = []
    for paragraph in paragraph74:
        ifrc_project_manager.append(paragraph.text)
    data['ifrc_project_manager_title'] = ifrc_project_manager[3]
    data['ifrc_project_manager_email'] = ifrc_project_manager[5]
    data['ifrc_project_manager_phone_number'] = ifrc_project_manager[7]
    data['ifrc_project_manager_name'] = ifrc_project_manager[0]

    paragraph75 = document.paragraphs[75]._element.xpath('.//w:t')
    ifrc_emergency = []
    for paragraph in paragraph75:
        ifrc_emergency.append(paragraph.text)
    data['ifrc_emergency_title'] = ifrc_emergency[3]
    data['ifrc_emergency_email'] = ifrc_emergency[5]
    data['ifrc_emergency_phone_number'] = ifrc_emergency[7]
    data['ifrc_emergency_name'] = ifrc_emergency[0]

    paragraph76 = document.paragraphs[76]._element.xpath('.//w:t')
    media = []
    for paragraph in paragraph76:
        media.append(paragraph.text)
    data['media_contact_title'] = media[3]
    data['media_contact_email'] = media[5]
    data['media_contact_phone_number'] = media[7]
    data['media_contact_name'] = media[0]

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
    # Create dref objects
    # map m2m fields
    data['is_published'] = False
    data['national_society'] = Country.objects.first()
    data['created_by'] = created_by
    dref = Dref.objects.create(**data)
    return dref
