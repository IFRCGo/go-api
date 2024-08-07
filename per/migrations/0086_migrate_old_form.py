# Generated by Django 3.2.20 on 2023-09-27 05:07

from django.core.management import call_command
from django.db import migrations


class Migration(migrations.Migration):

    def forwards_func(apps, schema_editor):
        print("forwards")
        call_command("loaddata", "componentratings.json", verbosity=2)

    def reverse_func(apps, schema_editor):
        print("reverse")

    def migrate_data(apps, schema_editor):
        Form = apps.get_model("per", "Form")
        FormData = apps.get_model("per", "FormData")
        FormComponentQuestionAndAnswer = apps.get_model("per", "FormComponentQuestionAndAnswer")
        FormComponent = apps.get_model("per", "FormComponent")
        FormComponentResponse = apps.get_model("per", "FormComponentResponse")
        AreaResponse = apps.get_model("per", "AreaResponse")
        PerAssessment = apps.get_model("per", "PerAssessment")
        PerComponentRating = apps.get_model("per", "PerComponentRating")

        per_assessments_by_overview = {}

        for form in Form.objects.all():
            overview = form.overview
            per_assessment = per_assessments_by_overview.get(overview.id)

            if not per_assessment:
                per_assessment = PerAssessment.objects.create(
                    overview=overview,
                    user=form.user,
                    is_draft=True,
                )

                per_assessments_by_overview[overview.id] = per_assessment

            area = form.area
            area_response = AreaResponse.objects.create(area=form.area)
            per_assessment.area_responses.add(area_response)

            rating_map = {3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6}

            for component_response in area.formcomponent_set.all():
                form_component_response = FormComponentResponse.objects.create(
                    component=component_response,
                )
                area_response.component_response.add(form_component_response)

                form_data_entries = FormData.objects.filter(form=form, question__component=component_response)

                for form_data_entry in form_data_entries:
                    question = form_data_entry.question.question
                    answer = form_data_entry.selected_answer
                    notes = form_data_entry.notes_en
                    if answer:
                        if question != "Component performance" and answer.id in [1, 2]:
                            question_and_answer = FormComponentQuestionAndAnswer.objects.create(
                                question=form_data_entry.question,
                                answer=form_data_entry.selected_answer,
                                notes=form_data_entry.notes_en,
                            )
                            form_component_response.question_responses.add(question_and_answer)
                    question = form_data_entry.question.question
                    if question == "Component performance":
                        answer = form_data_entry.selected_answer
                        if answer:
                            rating = rating_map.get(answer.id)
                            if rating is not None:
                                form_component_response.rating = PerComponentRating.objects.get(id=rating)
                                form_component_response.save(update_fields=["rating"])
                            else:
                                print(f"No rating found for answer {answer}")

    dependencies = [
        ("per", "0085_alter_overview_assessment_method"),
    ]

    operations = [
        # migrations.RunPython(forwards_func, reverse_func, elidable=False),
        migrations.RunPython(migrate_data, reverse_code=migrations.RunPython.noop),
    ]
