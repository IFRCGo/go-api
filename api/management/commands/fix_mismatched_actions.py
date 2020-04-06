from django.core.management.base import BaseCommand
import json

def get_by_org(actions, org):
    return list(filter(lambda a: org in a['organizations'], actions))

def get_by_type(actions, typ):
    return list(filter(lambda a: typ in a['field_report_types'], actions))

class Command(BaseCommand):
    help = 'Fixes mismatched actions in db'
    def handle(self, *args, **options):
        actions_file_path = 'data/actions_snapshot_staging.json'
        actions_data = json.load(open(actions_file_path))
        actions = actions_data['results']
        ORGANIZATIONS = ['NTLS', 'PNS', 'FDRN']
        REPORT_TYPES = ['EVT', 'EW']
        actions_by_org = {}
        mappings = {}
        for org in ORGANIZATIONS:
            actions_by_org[org] = {
                'all': get_by_org(actions, org)
            }
        for report_type in REPORT_TYPES:
            for org in ORGANIZATIONS:
                actions_by_org[org][report_type] = get_by_type(actions_by_org[org]['all'], report_type)
        for org in ORGANIZATIONS:
            mappings[org] = {}
            for report_type in REPORT_TYPES:
                mappings[org][report_type] = []
                all_actions = actions_by_org[org]['all']
                type_actions = actions_by_org[org][report_type]

                for index, action in enumerate(type_actions):
                    new = action
                    old = all_actions[index]
                    mapping = {
                        'old': old,
                        'new': new
                    }
                    if old['id'] != new['id']:
                        mappings[org][report_type].append(mapping)

        print(json.dumps(mappings, indent=2))