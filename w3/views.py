from django.shortcuts import render
import json, datetime, pytz
from django.http import JsonResponse
from api.views import (
    bad_request,
    bad_http_request,
    PublicJsonPostView,
    PublicJsonRequestView,
)
from .models import (
    ProgrammeTypes,
    Sectors,
    Statuses,
    Project
)

# Create your views here.

class CreateProject(PublicJsonPostView):
    def handle_post(self, request, *args, **kwargs):
        body = json.loads(request.body.decode('utf-8'))
        required_fields = [
            'user_id',
            'reporting_ns',
            'project_district',
            'name',
        ]
        missing_fields = [field for field in required_fields if field not in body]
        if len(missing_fields):
            return bad_request('Could not complete request due to missing mandatory field. Please submit %s' % ', '.join(missing_fields))

        currentDT = datetime.datetime.now(pytz.timezone('UTC'))
        if 'programme_type' not in body:
            body['programme_type'] = ProgrammeTypes.MULTILATERAL
        if 'sector' not in body:
            body['sector'] = Sectors.WASH
        if 'start_date' not in body:
            body['start_date']   = str(currentDT)
        if 'end_date' not in body:
            body['end_date']   = str(currentDT)
        if 'budget_amount' not in body:
            body['budget_amount'] = 0
        if 'status' not in body:
            body['status'] = Statuses.ONGOING
        project = Project.objects.create(user_id           = body['user_id'],
                                         reporting_ns      = body['reporting_ns'],
                                         project_district  = body['project_district'],
                                         name              = body['name'],
                                         programme_type    = body['programme_type'],
                                         sector            = body['sector'],
                                         start_date        = body['start_date'],
                                         end_date          = body['end_date'],
                                         budget_amount     = body['budget_amount'],
                                         status            = body['status'],
                                         )
        try:
            project.save()
        except:
            return bad_request('Could not create Project record.')
        return JsonResponse({'status': 'ok'})
