import csv
import os

from django.conf import settings
from rest_framework import views
from rest_framework.response import Response


class ProBonoServicesView(views.APIView):
    """
    API endpoint to serve Pro Bono Services data from CSV file
    """

    permission_classes = []  

    def get(self, request):
        """
        Read Pro Bono CSV and return as JSON
        """
        csv_path = os.path.join(settings.BASE_DIR, 'data', 'ProBono.csv')
        
        if not os.path.exists(csv_path):
            return Response({'results': []})
        
        results = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for idx, row in enumerate(reader, start=1):
                    results.append({
                        'id': idx,
                        'company': row.get('Company', ''),
                        'name1': row.get('Name 1', ''),
                        'email1': row.get('Email address 1', ''),
                        'name2': row.get('Name 2', ''),
                        'email2': row.get('Email address 2', ''),
                        'services': row.get('Transport means and services', ''),
                        'comments': row.get('Comments', ''),
                    })
        except Exception as e:
            return Response({
                'error': f'Failed to read CSV file: {str(e)}',
                'results': []
            }, status=500)
        
        return Response({'results': results})
