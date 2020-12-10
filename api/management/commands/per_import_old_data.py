import csv
from django.db import transaction
from django.core.management.base import BaseCommand
from per.models import AssessmentType, FormArea, FormComponent, FormQuestion, FormAnswer


class Command(BaseCommand):
    help = 'Imports old PER translations from CSV'
    missing_args_message = "filename, type or areanum are missing"

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs='+', type=str)
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
        filename = kwargs['filename'][0]
        objtype = kwargs['type']
        area_num = kwargs['areanum'][0] if kwargs['areanum'] else ''

        if objtype == 'atypes':
            is_empty = not AssessmentType.objects.exists()
            if is_empty:
                AssessmentType.objects.create(name='Self assessment', name_en='Self assessment')
                AssessmentType.objects.create(name='Simulation', name_en='Simulation')
                AssessmentType.objects.create(name='Operational', name_en='Operational')
                AssessmentType.objects.create(name='Post operational', name_en='Post operational')

        try:
            with open(filename, 'r') as f:
                reader = csv.reader(f, delimiter=',')
                fieldnames = next(reader)
                rows = list(reader)

                if objtype == 'areas':
                    for row in rows:
                        FormArea.objects.create(**{
                            fieldnames[0]: row[0],
                            fieldnames[1]: row[1],
                            fieldnames[2]: row[2],
                            fieldnames[3]: row[3],
                            fieldnames[4]: row[4],
                            fieldnames[5]: row[5]
                        })
                elif objtype == 'components':
                    for row in rows:
                        area = FormArea.objects.filter(area_num=area_num).first()
                        if area:
                            FormComponent.objects.create(**{
                                'area_id': area.id,
                                fieldnames[0]: row[0],
                                fieldnames[1]: row[1],
                                fieldnames[2]: row[2],
                                fieldnames[3]: row[3],
                                fieldnames[4]: row[4],
                                fieldnames[5]: row[5],
                                fieldnames[6]: row[6],
                                fieldnames[7]: row[7],
                                fieldnames[8]: row[8],
                                fieldnames[9]: row[9],
                                fieldnames[10]: row[10],
                                fieldnames[11]: row[11]
                            })
                elif objtype == 'questions':
                    answers = FormAnswer.objects.all()
                    yes = answers.filter(text__iexact='yes').first()
                    no = answers.filter(text__iexact='no').first()
                    not_reviewed = answers.filter(text__iexact='not reviewed').first()
                    does_not_exist = answers.filter(text__iexact='does not exist').first()
                    partially = answers.filter(text__iexact='partially exists').first()
                    need_improv = answers.filter(text__iexact='need improvements').first()
                    exist = answers.filter(text__iexact='exist, could be strengthened').first()
                    high_performance = answers.filter(text__iexact='high performance').first()

                    prev_comp_num = 0
                    prev_comp_letter = ''
                    for row in rows:
                        if not row[0] and not row[1]:
                            continue

                        comp_num = row[0]
                        comp_letter = row[1]
                        comp = FormComponent.objects.filter(component_num=comp_num, component_letter=comp_letter).first()
                        if comp:
                            question = FormQuestion.objects.create(**{
                                'component_id': comp.id,
                                fieldnames[2]: row[2],
                                fieldnames[3]: row[3],
                                fieldnames[4]: row[4],
                                fieldnames[5]: row[5],
                                fieldnames[6]: row[6],
                                fieldnames[7]: row[7]
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
