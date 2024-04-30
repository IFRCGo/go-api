# Generated by Django 3.2.23 on 2024-01-30 08:51

from django.db import migrations
from api.logger import logger


class Migration(migrations.Migration):

    def migrate_component_to_question_group(apps, schema_editor):
        FormComponent = apps.get_model('per', 'FormComponent')
        FormQuestionGroup = apps.get_model('per', 'FormQuestionGroup')
        FormQuestion = apps.get_model('per', 'FormQuestion')
        FormComponentResponse = apps.get_model('per', 'FormComponentResponse')

        # Fetch components to migrate
        to_migrate_component_ids = [53, 52, 51, 50, 49]
        to_migrate_components = FormComponent.objects.filter(id__in=to_migrate_component_ids)

        # Create question groups
        question_group_count = 0
        for component in to_migrate_components:
            question_group = FormQuestionGroup.objects.create(
                title_en=component.title_en,
                title_es=component.title_es,
                title_ar=component.title_ar,
                title_fr=component.title_fr,
                description_en=component.description_en,
                description_es=component.description_es,
                description_ar=component.description_ar,
                description_fr=component.description_fr,
                component_id=48
            )
            question_group_count += 1

        logger.info(f'Created QuestionGroup count {question_group_count}')

        # Attach questions to question groups
        form_questions_to_migrate = FormQuestion.objects.filter(component_id__in=to_migrate_component_ids)
        question_count = 0
        for question in form_questions_to_migrate:
            form_question_group = FormQuestionGroup.objects.filter(
                title_en=question.component.title_en
            )
            if form_question_group.exists():
                form_question_group_first = form_question_group.first()
                question.question_group = form_question_group_first
                question.save(update_fields=['question_group'])
                question_count += 1

        logger.info(f'Attached Question count {question_count}')

        # Update component responses
        FormComponentResponse.objects.filter(component_id__in=to_migrate_component_ids).update(component_id=48)

        # Update component ID for old data
        form_questions_to_migrate.update(component_id=48)

        #Delete old form components
        deleted_count, _ = to_migrate_components.delete()
        print(f'Deleted {deleted_count} FormComponent instances')


    dependencies = [
        ('per', '0099_auto_20240130_0850'),
    ]

    operations = [
        migrations.RunPython(
            migrate_component_to_question_group,
            reverse_code=migrations.RunPython.noop
        ),
    ]
