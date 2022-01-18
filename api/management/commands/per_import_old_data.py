import csv
from django.db import transaction
from django.core.management.base import BaseCommand
from per.models import AssessmentType, FormArea, FormComponent, FormQuestion, FormAnswer


class Command(BaseCommand):
    help = 'Imports old PER translations from CSV'
    missing_args_message = "filename, type or areanum are missing"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='?', type=str)
        parser.add_argument(
            '-t',
            '--type',
            type=str,
            help='Type must be one of the following: atypes, areas, components, questions'
        )
        parser.add_argument(
            '-a',
            '--areanum',
            type=str,
            help='Area number must be an integer'
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        filename = kwargs['filename'] if kwargs['filename'] else ''
        objtype = kwargs['type']
        area_num = kwargs['areanum'][0] if kwargs['areanum'] else ''

        if objtype == 'answers':
            is_empty = not FormAnswer.objects.exists()
            if is_empty:
                FormAnswer.objects.create(text='yes', text_en='yes')
                FormAnswer.objects.create(text='no', text_en='no')
                FormAnswer.objects.create(text='Not Reviewed', text_en='Not Reviewed')
                FormAnswer.objects.create(text='Does not exist', text_en='Does not exist')
                FormAnswer.objects.create(text='Partially exists', text_en='Partially exists')
                FormAnswer.objects.create(text='Needs improvement', text_en='Needs improvement')
                FormAnswer.objects.create(text='Exists, could be strengthened', text_en='Exists, could be strengthened')
                FormAnswer.objects.create(text='High performance', text_en='High performance')
                print('done!')
            else:
                print('per_formanswer table is not empty')
            return

        if objtype == 'atypes':
            is_empty = not AssessmentType.objects.exists()
            if is_empty:
                AssessmentType.objects.create(name='Self assessment', name_en='Self assessment')
                AssessmentType.objects.create(name='Simulation', name_en='Simulation')
                AssessmentType.objects.create(name='Operational', name_en='Operational')
                AssessmentType.objects.create(name='Post operational', name_en='Post operational')
                print('done!')
            else:
                print('per_assessmenttype table is not empty')
            return

        try:
            if not filename:
                print('FAILED, filename is empty')
                return
            if not objtype:
                print('FAILED, --type is empty')
                return

            with open(filename, 'r') as f:
                reader = csv.reader(f, delimiter=',')
                fieldnames = next(reader)
                rows = list(reader)

                if objtype == 'areas':
                    for row in rows:
                        FormArea.objects.create(**{
                            fieldnames[0]: row[0],  # area_num
                            fieldnames[1]: row[1],  # title
                            fieldnames[2]: row[2],  # title_en
                            fieldnames[3]: row[3],  # title_fr
                            fieldnames[4]: row[4],  # title_es
                            fieldnames[5]: row[5]  # title_ar
                        })
                elif objtype == 'components':
                    if not area_num:
                        print('FAILED, --areanum is empty')

                    for row in rows:
                        area = FormArea.objects.filter(area_num=area_num).first()
                        if area:
                            FormComponent.objects.create(**{
                                'area_id': area.id,
                                fieldnames[0]: row[0],  # component_num
                                fieldnames[1]: row[1],  # component_letter
                                fieldnames[2]: row[2],  # title
                                fieldnames[3]: row[3],  # title_en
                                fieldnames[4]: row[4],  # title_fr
                                fieldnames[5]: row[5],  # title_es
                                fieldnames[6]: row[6],  # title_ar
                                fieldnames[7]: row[7],  # description
                                fieldnames[8]: row[8],  # description_en
                                fieldnames[9]: row[9],  # description_fr
                                fieldnames[10]: row[10],  # description_es
                                fieldnames[11]: row[11]  # description_ar
                            })
                elif objtype == 'questions':
                    answers = FormAnswer.objects.all()
                    yes = answers.filter(text__iexact='yes').first()
                    no = answers.filter(text__iexact='no').first()
                    not_reviewed = answers.filter(text__iexact='not reviewed').first()
                    does_not_exist = answers.filter(text__iexact='does not exist').first()
                    partially = answers.filter(text__iexact='partially exists').first()
                    need_improv = answers.filter(text__iexact='needs improvement').first()
                    exist = answers.filter(text__iexact='exists, could be strengthened').first()
                    high_performance = answers.filter(text__iexact='high performance').first()

                    prev_comp_num = 0
                    prev_comp_letter = ''
                    for row in rows:
                        # If Component number and letter are both empty, skip
                        if not row[0] and not row[1]:
                            continue

                        comp_num = row[0]
                        comp_letter = row[1]
                        # Component 34 has subcomponents but no letters to distinguish
                        if comp_num == '34':
                            question_num = int(row[2])
                            last_question = True if question_num == 32 else False

                            if question_num <= 7:
                                comp = FormComponent.objects.filter(title__iexact='LOGISTICS MANAGEMENT').first()
                            elif question_num <= 12:
                                comp = FormComponent.objects.filter(title__iexact='SUPPLY CHAIN MANAGEMENT').first()
                            elif question_num <= 17:
                                comp = FormComponent.objects.filter(title__iexact='PROCUREMENT').first()
                            elif question_num <= 28:
                                comp = FormComponent.objects.filter(title__iexact='FLEET AND TRANSPORTATION MANAGEMENT').first()
                            else:
                                comp = FormComponent.objects.filter(title__iexact='WAREHOUSE AND STOCK MANAGEMENT').first()

                            if comp:
                                question = FormQuestion.objects.create(**{
                                    'component_id': comp.id,
                                    fieldnames[2]: row[2],  # question_num
                                    fieldnames[3]: row[3],  # question
                                    fieldnames[4]: row[4],  # question_en
                                    fieldnames[5]: row[5],  # question_fr
                                    fieldnames[6]: row[6],  # question_es
                                    fieldnames[7]: row[7]  # question_ar
                                })

                                # By default only add yes-no answers
                                question.answers.add(yes, no)

                                if last_question:
                                    bench_q = FormQuestion.objects.create(
                                        component_id=comp.id,
                                        question='Component performance',
                                        is_benchmark=True
                                    )
                                    bench_q.answers.add(
                                        not_reviewed, does_not_exist, partially, need_improv, exist, high_performance
                                    )

                                    # Add EPI question
                                    epi_q = FormQuestion.objects.create(
                                        component_id=comp.id,
                                        question='Component Epidemic Preparedness',
                                        is_epi=True
                                    )
                                    epi_q.answers.add(
                                        not_reviewed, does_not_exist, partially, need_improv, exist, high_performance
                                    )
                        else:
                            comp = FormComponent.objects.filter(component_num=comp_num, component_letter=comp_letter).first()
                            if comp:
                                question = FormQuestion.objects.create(**{
                                    'component_id': comp.id,
                                    fieldnames[2]: row[2],  # question_num
                                    fieldnames[3]: row[3],  # question
                                    fieldnames[4]: row[4],  # question_en
                                    fieldnames[5]: row[5],  # question_fr
                                    fieldnames[6]: row[6],  # question_es
                                    fieldnames[7]: row[7]  # question_ar
                                })

                                # By default only add yes-no answers
                                question.answers.add(yes, no)

                                if prev_comp_num != comp_num or prev_comp_letter != comp_letter:
                                    prev_comp_num = comp_num
                                    prev_comp_letter = comp_letter
                                    # Add benchmark performance questions with relevant answers for each component
                                    bench_q = FormQuestion.objects.create(
                                        component_id=comp.id,
                                        question='Component performance',
                                        is_benchmark=True
                                    )
                                    bench_q.answers.add(
                                        not_reviewed, does_not_exist, partially, need_improv, exist, high_performance
                                    )

                                    # Add EPI question
                                    epi_q = FormQuestion.objects.create(
                                        component_id=comp.id,
                                        question='Component Epidemic Preparedness',
                                        is_epi=True
                                    )
                                    epi_q.answers.add(
                                        not_reviewed, does_not_exist, partially, need_improv, exist, high_performance
                                    )
            print('done!')
        except Exception as e:
            print('FAILED')
            print(e)
