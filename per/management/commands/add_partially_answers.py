from django.core.management.base import BaseCommand

from per.models import FormQuestion, FormAnswer


class Command(BaseCommand):
    help = 'Update Patially also as choice in assessment answer'

    def handle(self, *args, **options):
        form_questions = FormQuestion.objects.all()
        for form_question in form_questions:
            form_question.answers.add(FormAnswer.objects.get(id=5))  # Hardcoded for now
