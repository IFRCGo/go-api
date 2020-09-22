from .models import CronJob


def create_cron_record(name, msg, status, num_result=0):
    cron_obj = {
        'name': name,
        'message': msg,
        'num_result': num_result,
        'status': status
    }
    CronJob.sync_cron(cron_obj)
