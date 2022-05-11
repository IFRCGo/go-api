import datetime

import docx

from django.core.exceptions import ValidationError
from dref.models import (
    Dref,
    DrefCountryDistrict,
    PlannedIntervention,
    IdentifiedNeed,
    NationalSocietyAction,
)
from api.models import (
    DisasterType,
    Country,
    District
)


def parse_national_society_title(title):
    title_dict = {
        'National Society Readiness': NationalSocietyAction.Title.NATIONAL_SOCIETY_READINESS,
        'Assessments': NationalSocietyAction.Title.ASSESSMENT,
        'Coordination': NationalSocietyAction.Title.COORDINATION,
        'Resource Mobilization': NationalSocietyAction.Title.RESOURCE_MOBILIZATION,
        'Activation of contingency plans': NationalSocietyAction.Title.ACTIVATION_OF_CONTINGENCY_PLANS,
        'EOC': NationalSocietyAction.Title.NATIONAL_SOCIETY_EOC,
        'Shelter and Basic Household Needs': NationalSocietyAction.Title.SHELTER_AND_BASIC_HOUSEHOLD_ITEMS,
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
        'Shelter, Housing and Settlements': IdentifiedNeed.Title.SHELTER_AND_BASIC_HOUSEHOLD_ITEMS,
        'Multi-purpose Cash': IdentifiedNeed.Title.MULTI_PURPOSE_CASH_GRANTS,
        'Protection, Gender, and Inclusion (PGI)': IdentifiedNeed.Title.PROTECTION_GENDER_AND_INCLUSION,
        'Education': IdentifiedNeed.Title.EDUCATION,
        'Migration': IdentifiedNeed.Title.MIGRATION,
        'Environmental Sustainability': IdentifiedNeed.Title.ENVIRONMENT_SUSTAINABILITY,
    }
    return title_dict.get(title)


def parse_planned_intervention_title(title):
    title_dict = {
        'Shelter, Housing and Settlements': PlannedIntervention.Title.SHELTER_AND_BASIC_HOUSEHOLD_ITEMS,
        'Livelihoods': PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS,
        'Multi-purpose Cash': PlannedIntervention.Title.MULTI_PURPOSE_CASH_GRANTS,
        'Health & Care': PlannedIntervention.Title.HEALTH,
        'Water, Sanitation and Hygiene': PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE,
        'Protection, Gender and Inclusion': PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION,
        'Education': PlannedIntervention.Title.EDUCATION,
        'Migration': PlannedIntervention.Title.MIGRATION,
        'Risk Reduction, climate adaptation and Recovery': PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,
        'Environmental Sustainability': PlannedIntervention.Title.ENVIRONMENT_SUSTAINABILITY,
    }
    return title_dict.get(title)


def is_valid_date(date):
    try:
        return datetime.datetime.strptime(date, '%d/%m/%Y')
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


def extract_file(doc):
    document = docx.Document(doc)
    data = {}
    # NOTE: Second Paragraph for Country and Region and Dref Title
    paragraph2 = document.paragraphs[1]
    paragraph_element2 = paragraph2._element.xpath('.//w:t')
    if len(paragraph_element2) > 0:
        element2 = paragraph_element2[0].text
        country = element2.split(',')
        country = Country.objects.get(name__icontains=country[0])
        region_title = country[1].split('|')
        district = District.objects.get(name__icontains=region_title[0])
        # TODO: Add check for validation of country and district
        if district.country != country:
            raise ValidationError('Found different district for provided country')
        data['title'] = region_title[1]
        # TODO: Add national_society when added on the document
    table = document.tables[0]
    table_row_zero_column_zero = table.cell(0 , 0)._tc.xpath('.//w:t')
    data['appeal_code'] = table_row_zero_column_zero[4].text
    table_row_zero_column_one = table.cell(0, 1)._tc.xpath('.//w:t')
    if len(table_row_zero_column_one) == 3:
        data['amount_requested'] = int(table_row_zero_column_one[2].text)
    table_row_one_column_zero = table.cell(1, 0)._tc.xpath('.//w:t')
    data['glide_no'] = table_row_one_column_zero[3].text
    table_row_one_column_one = table.cell(1, 1)._tc.xpath('.//w:t')
    if len(table_row_one_column_one) == 3:
        data['num_affected'] = int(table_row_one_column_one[1].text)
    table_row_one_column_two = table.cell(1, 2)._tc.xpath('.//w:t')
    data['num_assisted'] = int(table_row_one_column_two[1].text)
    table_row_two_column_one = table.cell(2, 1)._tc.xpath('.//w:t')
    data['dref_launched'] = is_valid_date(table_row_two_column_one[4].text)
    table_row_two_column_two = table.cell(2, 2)._tc.xpath('.//w:t')
    data['dref_ended'] = is_valid_date(table_row_two_column_two[2].text)
    table_row_two_column_three = table.cell(2, 3)._tc.xpath('.//w:t')
    if len(table_row_two_column_three) == 4:
        data['operation_timeframe'] = int(table_row_two_column_three[1].text)
    else:
        data['operation_timeframe'] = int(table_row_two_column_three[1].text)
    table_row_three_column_one = table.cell(3, 1)._tc.xpath('.//w:t')
    data['disaster_category'] = parse_disaster_category(table_row_three_column_one[1].text)
    table_row_three_column_two = table.cell(3, 2)._tc.xpath('.//w:t')
    data['disaster_type'] = parse_disaster_type(table_row_three_column_two[1].text)
    table_row_three_column_three = table.cell(3, 3)._tc.xpath('.//w:t')
    data['type_of_onset'] = parse_type_of_onset(table_row_three_column_three[1].text)
    table_row_four_column_one = table.cell(4, 1)._tc.xpath('.//w:t')
    table_affected_list = table_row_four_column_one[1::]
    affected_data = []
    for affected in table_affected_list:
        affected_data.append(affected.text)
    # Is this country_district
    #data['affected_areas'] = ''.join(affected_data) if affected_data else None

    paragraph5 = document.paragraphs[5]
    paragraph_element5 = paragraph5._element.xpath('.//w:t')
    description = []
    if len(paragraph_element5) > 0:
        for desc in paragraph_element5:
            description.append(desc.text)
    data['event_text'] = ''.join(description) if description else None
    # Previous Operation
    table1 = document.tables[1]
    data['affect_same_area'] = table1.cell(0, 1)._tc.xpath('.//w:t')
    data['affect_same_population'] = table1.cell(1, 1)._tc.xpath('.//w:t')
    data['ns_respond'] = table1.cell(2, 1)._tc.xpath('.//w:t')
    data['ns_request_fund'] = table1.cell(3, 1)._tc.xpath('.//w:t')
    data['ns_request_text'] = table1.cell(4, 1)._tc.xpath('.//w:t')
    data['dref_recurrent_text'] = table1.cell(5, 1)._tc.xpath('.//w:t')
    data['lesson_learned'] = table1.cell(6, 1)._tc.xpath('.//w:t')
    # Paragraph scope

    scope_paragraph = document.paragraphs[9]._element.xpath('.//w:t')
    score_paragraph_desc = []
    if len(scope_paragraph) > 0:
        for desc in scope_paragraph:
            score_paragraph_desc.append(desc.text)
    data['event_scope'] = ''.join(score_paragraph_desc) if score_paragraph_desc else None
    table2 = document.tables[2]
    # National Society
    national_society_actions = []
    table_row_zero_column_one = table2.cell(0, 0)._tc.xpath('.//w14:checkBox//w14:checked[@w14:val="1"]')
    if table_row_zero_column_one:
        title = table2.cell(1, 2)._tc.xpath('.//w:t')[0].text
        description = table2.cell(1, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_national_society_title(title),
            'description': ''.join(description_list)
        }
        national_society_actions.append(data_new)

    table3 = document.tables[3]
    table_row_zero_column_zero = table3.cell(0 , 1)._tc.xpath('.//w:t')
    ifrc_desc = []
    if len(table_row_zero_column_zero) > 0:
        for desc in table_row_zero_column_zero:
            ifrc_desc.append(desc.text.strip('"').replace(',', ''))
    data['ifrc'] = ifrc_desc
    table_row_one_column_one = table3.cell(1 , 1)._tc.xpath('.//w:t')
    icrc_desc = []
    if len(table_row_one_column_one) > 0:
        for desc in table_row_one_column_one:
            icrc_desc.append(desc.text.strip('"').replace(',', ''))
    data['icrc'] = icrc_desc
    table_row_two_column_two = table3.cell(2, 1)._tc.xpath('.//w:t')
    partner_national_society_desc = []
    if len(table_row_two_column_two) > 0:
        for partner in table_row_two_column_two:
            partner_national_society_desc.append(partner.text.strip('"').replace(',', ''))
    data['partner_national_society'] = partner_national_society_desc
    # Other actors
    table4 = document.tables[4]
    table_row_zero_column_zero = table4.cell(0 , 1)._tc.xpath('.//w:t')
    if len(table_row_one_column_one) > 0:
        data['government_requested_assistance'] = table_row_one_column_one[0]
    table_row_one_column_one = table4.cell(1 , 1)._tc.xpath('.//w:t')
    national_authorities = []
    if len(table_row_one_column_one) > 0:
        for authorities in table_row_one_column_one:
            national_authorities.append(authorities.text)
    data['national_authorities'] = ''.join(national_authorities)
    un_and_other_actors = []
    table_row_two_column_one = table4.cell(2 , 1)._tc.xpath('.//w:t')
    if len(table_row_two_column_one) > 0:
        for authorities in table_row_two_column_one:
            un_and_other_actors.append(authorities.text)
    data['un_or_other_actor'] = ''.join(un_and_other_actors)
    coordination_mechanism = []
    table_row_three_column_one = table4.cell(3, 1)._tc.xpath('.//w:t')
    if len(table_row_three_column_one) > 0:
        for coordination in table_row_three_column_one:
            coordination_mechanism.append(coordination.text)
    data['major_coordination_mechanism'] = ''.join(coordination_mechanism)
    # NeedsIdentified
    table5 = document.tables[5]
    table_row_zero_column_one = table5.cell(0, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    needs_identified = []
    if table_row_zero_column_one:
        title = table5.cell(0, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(0, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_one_column_one = table5.cell(1, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_one_column_one:
        title = table5.cell(1, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(1, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_two_column_one = table5.cell(2, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_two_column_one:
        title = table5.cell(2, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(2, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_three_column_one = table5.cell(3, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_three_column_one:
        title = table5.cell(3, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(3, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_four_column_one = table5.cell(4, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_four_column_one:
        title = table5.cell(3, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(3, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_five_column_one = table5.cell(5, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_five_column_one:
        title = table5.cell(5, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(5, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_six_column_one = table5.cell(6, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_six_column_one:
        title = table5.cell(6, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(6, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_seven_column_one = table5.cell(7, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_seven_column_one:
        title = table5.cell(7, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(7, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_eight_column_one = table5.cell(8, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_eight_column_one:
        title = table5.cell(8, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(8, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    table_row_nine_column_one = table5.cell(9, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_nine_column_one:
        title = table5.cell(9, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(9, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)
    """table_row_ten_column_one = table5.cell(10, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
    if table_row_ten_column_one:
        title = table5.cell(10, 2)._tc.xpath('.//w:t')[0].text
        description = table5.cell(10, 3)._tc.xpath('.//w:t')
        description_list = []
        if len(description) > 0:
            for desc in description:
                description_list.append(desc.text)
        data_new = {
            'title': parse_identified_need_title(title.strip()),
            'description': ''.join(description_list)
        }
        needs_identified.append(data_new)"""
    needs_identifieds = needs_identified
    needs = []
    for data in needs_identifieds:
        planned_object = IdentifiedNeed.objects.create(**data)
        needs.append(planned_object)
    # targeting strategy
    paragraph30 = document.paragraphs[30]._element.xpath('.//w:t')
    people_assisted = []
    for paragraph in paragraph30:
        people_assisted.append(paragraph.text)
    data['people_assisted'] = ''.join(people_assisted) if len(people_assisted) > 0 else None
    paragraph32 = document.paragraphs[32]._element.xpath('.//w:t')
    selection_criteria = []
    for paragraph in paragraph32:
        selection_criteria.append(paragraph.text)
    data['selection_criteria'] = ''.join(selection_criteria) if len(selection_criteria) > 0 else None
    paragraph36 = document.paragraphs[34]._element.xpath('.//w:t')
    entity_affected = []
    for paragraph in paragraph36:
        entity_affected.append(paragraph.text)
    data['entity_affected'] = ''.join(entity_affected) if len(entity_affected) > 0 else None
    # Targeting Population
    table5 = document.tables[6]
    table_row_zero_column_three = table5.cell(0, 3)._tc.xpath('.//w:t')
    data['women'] = int(table_row_zero_column_three[0].text) if len(table_row_zero_column_three) > 0 else None
    table_row_zero_column_five = table5.cell(0, 5)._tc.xpath('.//w:t')
    data['men'] = int(table_row_zero_column_five[0].text) if len(table_row_zero_column_five) > 0 else None
    table_row_one_column_two = table5.cell(1, 3)._tc.xpath('.//w:t')
    data['girls'] = int(table_row_one_column_two[0].text) if len(table_row_one_column_two) > 0 else None
    table_row_one_column_five = table5.cell(1, 5)._tc.xpath('.//w:t')
    data['boys'] = int(table_row_one_column_five[0].text) if len(table_row_one_column_five) > 0 else None
    table_row_two_column_two = table5.cell(2, 2)._tc.xpath('.//w:t')
    data['total'] = int(table_row_two_column_two[0].text) if len(table_row_two_column_two) > 0 else None
    table_row_three_column_two = table5.cell(3, 3)._tc.xpath('.//w:t')
    data['disability_people_per'] = float(table_row_three_column_two[0].text) if len(table_row_three_column_two) > 0 else None
    table_row_three_column_four = table5.cell(3, 5)._tc.xpath('.//w:t')
    data['people_per_urban'] = float(table_row_three_column_four[0].text) if len(table_row_three_column_four) > 0 else None
    table_row_four_column_two = table5.cell(4, 3)._tc.xpath('.//w:t')
    data['total_targeted_population'] = float(table_row_four_column_two[0].text) if len(table_row_four_column_two) > 0 else None
    paragraph38 = document.paragraphs[38]._element.xpath('.//w:t')
    overall_objectives = []
    for paragraph in paragraph38:
        overall_objectives.append(paragraph.text)
    data['operation_objective'] = ''.join(overall_objectives)
    paragraph42 = document.paragraphs[42]._element.xpath('.//w:t')
    response_strategy = []
    for paragraph in paragraph42:
        response_strategy.append(paragraph.text)
    data['response_strategy'] = ''.join(response_strategy)
    paragraph46 = document.paragraphs[46]._element.xml
    human_resources = []
    for paragraph in paragraph46:
        human_resources.append(paragraph.text)
    data['human_resource'] = ''.join(human_resources)
    surge_personnel_deployed = []
    paragraph48 = document.paragraphs[48]._element.xpath('.//w:t')
    for paragraph in paragraph48:
        surge_personnel_deployed.append(paragraph.text)
    data['surge_personnel_deployed'] = ''.join(surge_personnel_deployed) if len(surge_personnel_deployed) else None
    paragraph50 = document.paragraphs[50]._element.xpath('.//w:t')
    logistic_capacity_of_ns = []
    for paragraph in paragraph50:
        logistic_capacity_of_ns.append(paragraph.text)
    data['logistic_capacity_of_ns'] = ''.join(logistic_capacity_of_ns) if len(logistic_capacity_of_ns) > 0 else None
    safety_concerns = []
    paragraph52 = document.paragraphs[52]._element.xpath('.//w:t')
    for paragraph in paragraph52:
        safety_concerns.append(paragraph.text)
    data['safety_concerns'] = ''.join(safety_concerns) if len(safety_concerns) > 0 else None
    pmer = []
    paragraph54 = document.paragraphs[54]._element.xpath('.//w:t')
    for paragraph in paragraph54:
        pmer.append(paragraph.text)
    data['pmer'] = ''.join(pmer) if len(pmer) > 0 else None
    communication = []
    paragraph56 = document.paragraphs[56]._element.xpath('.//w:t')
    for paragraph in paragraph56:
        communication.append(paragraph.text)
    data['communication'] = ''.join(communication) if len(communication) > 0 else None
    paragraph72 = document.paragraphs[73]._element.xpath('.//w:t')
    national_society_contact = []
    for paragraph in paragraph72:
        national_society_contact.append(paragraph.text)
    national_society_contact_split = national_society_contact[1].split(',')
    data['national_society_contact_title'] = national_society_contact_split[1].strip()
    data['national_society_contact_email'] = national_society_contact_split[1].strip()
    data['national_society_contact_phone_number'] = national_society_contact_split[2].strip()
    data['national_society_contact_name'] = national_society_contact_split[0].strip()

    paragraph73 = document.paragraphs[74]._element.xpath('.//w:t')
    ifrc_appeal_manager = []
    for paragraph in paragraph73:
        ifrc_appeal_manager.append(paragraph.text)
    ifrc_appeal_manager_list = ifrc_appeal_manager[1].split(',')
    data['ifrc_appeal_manager_title'] = ifrc_appeal_manager_list[1].strip()
    data['ifrc_appeal_manager_email'] = ifrc_appeal_manager_list[2].strip()
    data['ifrc_appeal_manager_phone_number'] = ifrc_appeal_manager_list[3].strip()
    data['ifrc_appeal_manager_name'] = ifrc_appeal_manager_list[0].strip()
    paragraph74 = document.paragraphs[75]._element.xpath('.//w:t')
    ifrc_project_manager = []
    for paragraph in paragraph74:
        ifrc_project_manager.append(paragraph.text)
    ifrc_project_manager_list = ifrc_project_manager[1].split(',')
    data['ifrc_project_manager_title'] = ifrc_project_manager_list[1].strip()
    data['ifrc_project_manager_email'] = ifrc_project_manager_list[2].strip()
    data['ifrc_project_manager_phone_number'] = ifrc_project_manager_list[3].strip()
    data['ifrc_project_manager_name'] = ifrc_project_manager_list[0].strip()

    paragraph75 = document.paragraphs[76]._element.xpath('.//w:t')
    ifrc_emergency = []
    for paragraph in paragraph75:
        ifrc_emergency.append(paragraph.text)
    ifrc_emergency_list = ifrc_emergency[1].split(',')
    data['ifrc_emergency_title'] = ifrc_emergency_list[1].strip()
    data['ifrc_emergency_email'] = ifrc_emergency_list[2].strip()
    data['ifrc_emergency_phone_number'] = ifrc_emergency_list[3].strip()
    data['ifrc_emergency_name'] = ifrc_emergency_list[0].strip()

    paragraph76 = document.paragraphs[77]._element.xpath('.//w:t')
    media = []
    for paragraph in paragraph76:
        media.append(paragraph.text)
    media_list = media[1].split(',')
    data['media_title'] = media_list[1].strip()
    data['media_email'] = media_list[2].strip()
    data['media_phone_number'] = media_list[3].strip()
    data['media_name'] = media_list[0].strip()
    # PlannedIntervention Table
    planned_intervention = []
    for i in range(7, 17):
        table = document.tables[i]
        table_row_zero_column_one = table.cell(0, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
        if table_row_zero_column_one:
            title = table.cell(0, 1)._tc.xpath('.//w:t')[1].text
            budget = table.cell(0, 3)._tc.xpath('.//w:t')
            targated_population = table.cell(1, 3)._tc.xpath('.//w:t')

            indicator = table.cell(2, 3)._tc.xpath('.//w:t')
            indicators = []
            for indicator in indicators:
                indicators.append(indicator)
            indicator = ''.join(indicator) if len(indicators) > 0 else None
            priority_actions_list = []
            priority_actions = table.cell(3, 3)._tc.xpath('.//w:t')
            for priority_action in priority_actions:
                priority_actions_list.append(priority_action)
            priority_actions = ''.join(priority_actions_list) if len(priority_actions_list) > 0 else None
            planned = {
                'title': parse_planned_intervention_title(title),
                'budget': budget[0].text if len(budget) > 0 else None,
                'person_targeted': targated_population[0].text if len(targated_population) > 0 else None,
                'indicator': indicator,
                # 'priority_actions': priority_actions # NOTE: This is not in database field
            }
            planned_intervention.append(planned)
    planned_interventions = planned_intervention
    planned = []
    for data in planned_interventions:
        planned_object = PlannedIntervention.objects.create(**data)
        planned.append(planned_object)
    # Create dref objects
    # map m2m fields
    dref = Dref.objects.create(**data)
    dref.planned_interventions.add(planned)
    dref.needs_identified.add(needs)
    dref.national_society_actions.add(national_society_actions)
    country_district = DrefCountryDistrict.objects.create(
        country=country,
    )
    country_district.district.add(district)
