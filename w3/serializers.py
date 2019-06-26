from rest_framework import serializers
from .models import Project, Currencies

class ProjectSerializer(serializers.ModelSerializer):
    budget_currency = Currencies.toJSON(Project.budget_currency)
    class Meta:
        model = Project
        fields = '__all__'
