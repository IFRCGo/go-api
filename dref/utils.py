import os
import zipfile
import datetime

import docx
from docx.oxml.ns import qn

from django.conf import settings
from dref.models import Dref, PlannedIntervention
from api.models import DisasterType


def import_images(doc):
    img_dir = os.path.join(settings.MEDIA_ROOT, 'images')

    # Create directory to save all image files if it doesn't exist
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    # Extract all images from .docx
    with zipfile.ZipFile(doc.file, 'r') as zipFile:
        filelist = zipFile.namelist()
        for filename in filelist:
            if filename.startswith('word/media/'):
                zipFile.extract(filename, path=img_dir)

    return img_dir


def relate_images(img_dir, doc_file):
    rels = {}
    for r in doc_file.part.rels.values():
        if isinstance(r._target, docx.parts.image.ImagePart):
            img = os.path.basename(r._target.partname)
            rels[r.rId] = img
    return rels


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
    img_dir = import_images(doc)
    rels = relate_images(img_dir, document)
    data = {}
    # NOTE: Second Paragraph for Country and Region and Dref Title
    paragraph2 = document.paragraphs[1]
    paragraph_element2 = paragraph2._element.xpath('.//w:t')
    if len(paragraph_element2) > 0:
        element2 = paragraph_element2[0].text
        country_region_new = element2.split(',')
        data['country'] = country_region_new[0]
        data['region'] = country_region_new[1]
        data['title'] = paragraph_element2[2].text
    images = []
    for paragraph in document.paragraphs:
        if 'graphicData' in paragraph._p.xml:
            for rId in rels:
                if rId in paragraph._p.xml:
                    image = os.path.join(settings.MEDIA_URL, 'images/word/media', rels[rId])
            images.append(image)
    data['image'] = images[0]
    table = document.tables[0]
    table_row_zero_column_zero = table.cell(0 , 0)._tc.xpath('.//w:t')
    if len(table_row_zero_column_zero) == 6:
        data['appeal_code'] = table_row_zero_column_zero[4].text + table_row_zero_column_zero[5].text
    table_row_zero_column_one = table.cell(0, 1)._tc.xpath('.//w:t')
    if len(table_row_zero_column_one) == 6:
        data['dref_allocated'] = int(table_row_zero_column_one[5].text)
    elif len(table_row_zero_column_one) == 4:
        data['dref_allocated'] = int(table_row_zero_column_one[3].text)
    table_row_one_column_zero = table.cell(1, 0)._tc.xpath('.//w:t')
    if len(table_row_zero_column_one) == 6:
        data['glide_no'] = table_row_one_column_zero[3].text + table_row_one_column_zero[4].text + table_row_one_column_zero[5].text
    table_row_one_column_one = table.cell(1, 1)._tc.xpath('.//w:t')
    if len(table_row_one_column_one) == 4:
        data['people_affected'] = int(table_row_one_column_one[1].text)
    elif len(table_row_one_column_one) == 2:
        data['people_affected'] = int(table_row_one_column_one[1].text)
    table_row_one_column_two = table.cell(1, 2)._tc.xpath('.//w:t')
    if len(table_row_one_column_two) == 5:
        data['people_assisted'] = int(table_row_one_column_two[1].text)
    else:
        data['people_assisted'] = int(table_row_one_column_two[1].text)
    table_row_two_column_one = table.cell(2, 1)._tc.xpath('.//w:t')
    data['dref_launched'] = is_valid_date(table_row_two_column_one[4].text)
    table_row_two_column_two = table.cell(2, 2)._tc.xpath('.//w:t')
    data['dref_ended'] = is_valid_date(table_row_two_column_two[2].text)
    table_row_two_column_three = table.cell(2, 3)._tc.xpath('.//w:t')
    if len(table_row_two_column_three) == 5:
        data['operation_timeframe'] = int(table_row_two_column_three[2].text)
    else:
        data['operation_timeframe'] = int(table_row_two_column_three[2].text)
    table_row_three_column_one = table.cell(3, 1)._tc.xpath('.//w:t')
    data['disaster_category'] = parse_disaster_category(table_row_three_column_one[1].text)
    table_row_three_column_two = table.cell(3, 2)._tc.xpath('.//w:t')
    data['disaster_category'] = parse_disaster_type(table_row_three_column_two[1].text)
    table_row_three_column_three = table.cell(3, 3)._tc.xpath('.//w:t')
    data['type_of_onset'] = parse_type_of_onset(table_row_three_column_three[1].text)
    table_row_four_column_one = table.cell(4, 1)._tc.xpath('.//w:t')
    table_affected_list = table_row_four_column_one[1::]
    affected_data = []
    for affected in table_affected_list:
        affected_data.append(affected.text.strip('"').replace(',', ''))
    data['affected_areas'] = affected_data

    paragraph5 = document.paragraphs[5]
    paragraph_element5 = paragraph5._element.xpath('.//w:t')
    description = []
    if len(paragraph_element5) > 0:
        for desc in paragraph_element5:
            description.append(desc.text)
    data['event_description'] = ''.join(description) if description else None
    # Previous Operation
    affect_same_population = []
    for table_std in document.tables[1]._element.xpath('.//w:sdt'):
        for std in table_std.xpath('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}):
            affect_same_population.append(std.text)
    data['affect_same_population'] = affect_same_population[0].lower() if len(affect_same_population) > 0 else None
    # TODO: Left with `Scope and Scale`
    # TODO: Left with Previous Action and National Society Action
    # MOVEMENT PARTNERS Actions
    # this is a table for national society actions
    table2 = document.tables[2]
    national_society_actions = []
    for row in table2.rows:
        for cell in row.cells:
            checkBoxes = cell._tc.xpath('.//w:checkBox//w:default[@w:val="0"]')
            if checkBoxes:
                national_society_actions.append(cell.text)
    data['national_society_actions'] = national_society_actions if len(national_society_actions) > 0 else None

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
    data['un_and_other_actors'] = ''.join(un_and_other_actors)
    coordination_mechanism = []
    table_row_three_column_one = table4.cell(3, 1)._tc.xpath('.//w:t')
    if len(table_row_three_column_one) > 0:
        for coordination in table_row_three_column_one:
            coordination_mechanism.append(coordination.text)
    data['major_coordination_mechanism'] = ''.join(coordination_mechanism)
    # NeedsIdentified
    table5 = document.tables[5]
    """for i in range(0, len(table5.rows) + 1):
        table_row_zero_column_one = table5.cell(i, 1)._tc.xpath('.//w:checkBox//w:default[@w:val="1"]')
        print(table_row_zero_column_one)
        needs_identified = []
        if table_row_zero_column_one:
            title = table5.cell(i, 2)._tc.xpath('.//w:t')[0].text
            description = table5.cell(i, 3)._tc.xpath('.//w:t')
            description_list = []
            if len(description) > 0:
                for desc in description:
                    description_list.append(desc.text)
            data_new = {
                'title': title,
                'description': ''.join(description_list)
            }
            needs_identified.append(data_new)
    print(needs_identified)"""


    # targeting strategy
    paragraph22 = document.paragraphs[22]._element.xpath('.//w:t')
    people_assisted = []
    for paragraph in paragraph22:
        people_assisted.append(paragraph.text)
    data['people_assisted'] = ''.join(people_assisted) if len(people_assisted) > 0 else None
    paragraph24 = document.paragraphs[24]._element.xpath('.//w:t')
    selection_criteria = []
    for paragraph in paragraph24:
        selection_criteria.append(paragraph.text)
    data['selection_criteria'] = ''.join(selection_criteria) if len(selection_criteria) > 0 else None
    paragraph26 = document.paragraphs[26]._element.xpath('.//w:t')
    entity_affected = []
    for paragraph in paragraph26:
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
    data['displaced_people'] = float(table_row_four_column_two[0].text) if len(table_row_four_column_two) > 0 else None
    paragraph30 = document.paragraphs[30]._element.xpath('.//w:t')
    overall_objectives = []
    for paragraph in paragraph30:
        overall_objectives.append(paragraph.text)
    data['operation_objectives'] = ''.join(overall_objectives)
    paragraph32 = document.paragraphs[33]._element.xpath('.//w:t')
    response_strategy = []
    for paragraph in paragraph32:
        response_strategy.append(paragraph.text)
    data['response_strategy'] = ''.join(response_strategy)
    paragraph38 = document.paragraphs[38]._element.xpath('.//w:t')
    human_resource = []
    for paragraph in paragraph38:
        human_resource.append(paragraph.text)
    data['human_resource'] = ''.join(human_resource) if len(human_resource) > 0 else None
    surge_personnel_deployed = []
    paragraph40 = document.paragraphs[40]._element.xpath('.//w:t')
    for paragraph in paragraph40:
        surge_personnel_deployed.append(paragraph.text)
    data['surge_personnel_deployed'] = ''.join(surge_personnel_deployed) if len(surge_personnel_deployed) else None
    paragraph42 = document.paragraphs[42]._element.xpath('.//w:t')
    logistic_capacity_of_ns = []
    for paragraph in paragraph42:
        logistic_capacity_of_ns.append(paragraph.text)
    data['logistic_capacity_of_ns'] = ''.join(logistic_capacity_of_ns) if len(logistic_capacity_of_ns) > 0 else None
    safety_concerns = []
    paragraph44 = document.paragraphs[44]._element.xpath('.//w:t')
    for paragraph in paragraph44:
        safety_concerns.append(paragraph.text)
    data['safety_concerns'] = ''.join(safety_concerns) if len(safety_concerns) > 0 else None
    pmer = []
    paragraph46 = document.paragraphs[46]._element.xpath('.//w:t')
    for paragraph in paragraph46:
        pmer.append(paragraph.text)
    data['pmer'] = ''.join(pmer) if len(pmer) > 0 else None
    communication = []
    paragraph48 = document.paragraphs[48]._element.xpath('.//w:t')
    for paragraph in paragraph48:
        communication.append(paragraph.text)
    data['communication'] = ''.join(communication) if len(communication) > 0 else None

    paragraph64 = document.paragraphs[64]._element.xpath('.//w:t')
    national_society_contact = []
    for paragraph in paragraph64:
        national_society_contact.append(paragraph.text)
    data['national_society_contact_title'] = national_society_contact[2].strip()
    data['national_society_contact_email'] = national_society_contact[3].strip()
    data['national_society_contact_phone_number'] = national_society_contact[3].strip()
    data['national_society_contact_name'] = national_society_contact[1].strip()

    paragraph65 = document.paragraphs[65]._element.xpath('.//w:t')
    ifrc_appeal_manager = []
    for paragraph in paragraph65:
        ifrc_appeal_manager.append(paragraph.text)
    ifrc_appeal_manager_list = ifrc_appeal_manager[2].split(',')
    data['ifrc_appeal_manager_title'] = ifrc_appeal_manager_list[1].strip()
    data['ifrc_appeal_manager_email'] = ifrc_appeal_manager_list[2].strip()
    data['ifrc_appeal_manager_phone_number'] = ifrc_appeal_manager_list[3].strip()
    data['ifrc_appeal_manager_name'] = ifrc_appeal_manager_list[0].strip()

    paragraph66 = document.paragraphs[66]._element.xpath('.//w:t')
    ifrc_project_manager = []
    for paragraph in paragraph66:
        ifrc_project_manager.append(paragraph.text)
    ifrc_project_manager_list = ifrc_project_manager[2].split(',')
    data['ifrc_project_manager_title'] = ifrc_project_manager_list[1].strip()
    data['ifrc_project_manager_email'] = ifrc_project_manager_list[2].strip()
    data['ifrc_project_manager_phone_number'] = ifrc_project_manager_list[3].strip()
    data['ifrc_project_manager_name'] = ifrc_project_manager_list[0].strip()

    paragraph67 = document.paragraphs[67]._element.xpath('.//w:t')
    ifrc_emergency = []
    for paragraph in paragraph67:
        ifrc_emergency.append(paragraph.text)
    ifrc_emergency_list = ifrc_emergency[3].split(',')
    data['ifrc_emergency_title'] = ifrc_emergency_list[1].strip()
    data['ifrc_emergency_email'] = ifrc_emergency_list[2].strip()
    data['ifrc_emergency_phone_number'] = ifrc_emergency_list[3].strip()
    data['ifrc_emergency_name'] = ifrc_emergency_list[0].strip()

    paragraph68 = document.paragraphs[68]._element.xpath('.//w:t')
    media = []
    for paragraph in paragraph68:
        media.append(paragraph.text)
    media_list = media[2].split(',')
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
                'title': title,
                'budget': budget[0].text if len(budget) > 0 else None,
                'person_targeted': targated_population[0].text if len(targated_population) > 0 else None,
                'indicator': indicator,
                #'priority_actions': priority_actions
            }
            planned_intervention.append(planned)
    data['planned_intervention'] = planned_intervention
    print(planned_intervention, "pppppppp")
    planned = []
    for data in planned_intervention:
        planned_object = PlannedIntervention.objects.create(**data)
        planned.append(planned_object)
    print(planned)
