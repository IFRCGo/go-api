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

DROP   TABLE if exists archived_not_sub;
CREATE TABLE archived_not_sub as select * from notifications_subscription;
BEGIN;
UPDATE      notifications_subscription set rtype=12, stype=0 where rtype=0; -- EVENT    > EMERGENCY
DELETE FROM notifications_subscription                       where rtype=0; -- EVENT    > EMERGENCY
UPDATE      notifications_subscription set rtype=13, stype=0 where rtype=1; -- APPEAL   >            OPERATION
DELETE FROM notifications_subscription                       where rtype=1; -- APPEAL   >            OPERATION
UPDATE      notifications_subscription set rtype=12, stype=0 where rtype=2; -- FIELDREP > EMERGENCY
DELETE FROM notifications_subscription                       where rtype=2; -- FIELDREP > EMERGENCY
COMMIT;

-- delete duplications (after merge):
BEGIN;
DELETE FROM notifications_subscription a USING notifications_subscription b
WHERE a.id < b.id
AND a.stype                   = b.stype
AND a.rtype                   = b.rtype
AND coalesce(a.lookup_id ,'') = coalesce(b.lookup_id  ,'')
AND coalesce(a.country_id, 0) = coalesce(b.country_id , 0)
AND coalesce(a.dtype_id  , 0) = coalesce(b.dtype_id   , 0)
AND coalesce(a.region_id , 0) = coalesce(b.region_id  , 0)
AND a.user_id                 = b.user_id
AND coalesce(a.event_id  , 0) = coalesce(b.event_id   , 0);
COMMIT;


CREATE OR REPLACE FUNCTION log_api_appeal_changes()
RETURNS TRIGGER AS $$
DECLARE datNow date = now();
BEGIN

   -- close current period
   UPDATE api_appealhistory SET valid_to = datNow where aid = OLD.aid; 
   
   -- insert a new period
   INSERT INTO api_appealhistory(appeal_id,valid_from, valid_to, num_beneficiaries, amount_requested, amount_funded, aid, start_date, end_date,atype, country_id, region_id)
   VALUES (NEW.id,datNow,'2200-01-01',NEW.num_beneficiaries,NEW.amount_requested,NEW.amount_funded,NEW.aid, NEW.start_date, NEW.end_date,NEW.atype, NEW.country_id, NEW.region_id);

   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE FUNCTION log_api_appeal_insterts()
RETURNS TRIGGER AS $$
DECLARE datNow date = now();
BEGIN

   -- insert a new period
   INSERT INTO api_appealhistory(appeal_id,valid_from, valid_to, num_beneficiaries, amount_requested, amount_funded, aid, start_date, end_date,atype, country_id, region_id)
   VALUES (NEW.id,datNow,'2200-01-01',NEW.num_beneficiaries,NEW.amount_requested,NEW.amount_funded,NEW.aid, NEW.start_date, NEW.end_date,NEW.atype, NEW.country_id, NEW.region_id);

   RETURN NEW;
END;
$$ language 'plpgsql';



DROP TRIGGER IF EXISTS tu_api_appeal_01 on api_appeal;
CREATE TRIGGER tu_api_appeal_01 BEFORE UPDATE
ON api_appeal FOR EACH ROW
-- we update real_data_update time only if important figures has been changed:
    WHEN ((OLD.num_beneficiaries IS DISTINCT FROM NEW.num_beneficiaries)
       OR (OLD.amount_requested  IS DISTINCT FROM NEW.amount_requested)
       OR (OLD.amount_funded     IS DISTINCT FROM NEW.amount_funded))
    EXECUTE PROCEDURE log_api_appeal_changes();


DROP TRIGGER IF EXISTS ti_api_appeal_01 on api_appeal;
CREATE TRIGGER ti_api_appeal_01 BEFORE INSERT
ON api_appeal FOR EACH ROW
    EXECUTE PROCEDURE log_api_appeal_insterts();


""")
        print("Db changes finished.");