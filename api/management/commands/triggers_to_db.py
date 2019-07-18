from django.db import connection
from django.core.management.base import BaseCommand
from django.conf import settings
from api.logger import logger
from main.frontend import frontend_url

class Command(BaseCommand):
    help = 'Set triggers for updating previous_updated fields in api_event, _appeal, _fieldreport tables'


    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute(
"""CREATE OR REPLACE FUNCTION update_previous_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.previous_update = OLD.updated_at; 
--             ^ here we use updated_at
   RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_api_event_change_previous on api_event;
CREATE TRIGGER update_api_event_change_previous BEFORE UPDATE
ON api_event FOR EACH ROW EXECUTE PROCEDURE update_previous_column();
-- here we use updated_at

DROP TRIGGER IF EXISTS update_api_fieldreport_change_previous on api_fieldreport;
CREATE TRIGGER update_api_fieldreport_change_previous BEFORE UPDATE
ON api_fieldreport FOR EACH ROW EXECUTE PROCEDURE update_previous_column();
-- here we use also updated_at
----------------------------------------------------------------------------
-- to have the really important appeal-data-updates:
CREATE OR REPLACE FUNCTION appeal_real_data_update()
RETURNS TRIGGER AS $$
BEGIN
   NEW.real_data_update = OLD.modified_at;
   NEW.previous_update = OLD.real_data_update;
   RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS check_appeal_data_update on api_appeal;
CREATE TRIGGER check_appeal_data_update BEFORE UPDATE
ON api_appeal FOR EACH ROW
-- we update real_data_update time only if important figures has been changed:
    WHEN ((OLD.num_beneficiaries IS DISTINCT FROM NEW.num_beneficiaries)
       OR (OLD.amount_requested  IS DISTINCT FROM NEW.amount_requested)
       OR (OLD.amount_funded     IS DISTINCT FROM NEW.amount_funded))
    EXECUTE PROCEDURE appeal_real_data_update();
""")
