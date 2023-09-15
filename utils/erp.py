import requests
import pytz
from itertools import chain
from datetime import datetime
from api.models import RequestChoices, ERPGUID
from api.logger import logger
from django.conf import settings


ERP_API_ENDPOINT = settings.ERP_API_ENDPOINT
ERP_API_SUBSCRIPTION_KEY = settings.ERP_API_SUBSCRIPTION_KEY


def push_fr_data(data, retired=False):
    if ERP_API_ENDPOINT == 'x':
        return
    # Contacts
    c_ifrc_names = ",".join(
        data.contacts.filter(ctype__iexact='Federation').values_list('name', flat=True)
    )  # normally there is only 1
    c_ns_names = ",".join(
        data.contacts.filter(ctype__iexact='NationalSociety').values_list('name', flat=True)
    )  # normally there is only 1

    requestTitle = data.event.name if data.event else '-'  # Emergency name

    try:
        countryNamesSet = set(
            country.iso for country in chain(data.event.countries.all(), data.countries.all())
        )  # Country ISO2 codes in emergency
        countryNames = list(countryNamesSet)
    except AttributeError:
        return

    if not countryNames:  # There is no use of empty countryNames = '[]', because on ERP side it is erroneous.
        return

    try:
        # Emergency DisasterStartDate: sometimes date, sometimes string (!FIXME somewhere else)
        disasterStartDate = data.event.disaster_start_date.strftime("%Y-%m-%d, %H:%M:%S")
    except AttributeError:
        disasterStartDate = (
            data.event.disaster_start_date
            if data.event
            else pytz.timezone("UTC").localize(datetime(1900, 1, 1, 1, 1, 1, 1)).strftime("%Y-%m-%d, %H:%M:%S")
        )

        '''
        InitialRequestType:
            If “Appeal” <> “No”, then “EA”.
            Else if “DREF” <> “No”, then “DREF”
            Else “Empty”
            (if both DREF and Appeal, then the type must be EA)
        '''

    if data.appeal != RequestChoices.NO:
        InitialRequestType, InitialRequestValue = "EA", data.appeal_amount
    elif data.dref != RequestChoices.NO:
        InitialRequestType, InitialRequestValue = "DREF", data.dref_amount
    else:
        InitialRequestType, InitialRequestValue = "Empty", 0

    # About "RecentAffected - 1" as index see (¤) in other code parts:
    index = data.recent_affected - 1 if data.recent_affected > 0 else 0
    # In Early Warning we use "potentially affected", not the normal "affected" figure. Should be only one:
    NumberOfPeopleAffected = [
        data.num_affected,
        data.gov_num_affected,
        data.other_num_affected,
        data.num_potentially_affected,
        data.gov_num_potentially_affected,
        data.other_num_potentially_affected][index]

    # index == 0 means undefined. So we estimate it:
    MaxNumberOfPeopleAffected = max(
        data.num_affected or 0,
        data.gov_num_affected or 0,
        data.other_num_affected or 0,
        data.num_potentially_affected or 0,
        data.gov_num_potentially_affected or 0,
        data.other_num_potentially_affected or 0)

    if index == 0 and 0 < MaxNumberOfPeopleAffected:
        NumberOfPeopleAffected = MaxNumberOfPeopleAffected

    payload = {
        "Emergency": {
            "EmergencyId": 0 if data.event_id is None else data.event_id,  # Emergency ID, RequestId
            "EmergencyTitle": requestTitle,  # Emergency name, RequestTitle
            "DisasterStartDate": disasterStartDate,  # Emergency DisasterStartDate
            "DisasterTypeId": data.dtype.name,  # dtype name. Not dtype_id!
            "DataAreaId": "ifrc",
            "FieldReport": {
                "RequestRetired": retired,  # Not sure if this will be needed/used at all
                "FieldReportId": data.id,  # Field Report ID, GORequestId
                "ReportedDateTime": data.updated_at.strftime("%Y-%m-%d, %H:%M:%S"),  # Field Report Updated at !!!FIXME!!!
                "RequestCreationDate": data.created_at.strftime("%Y-%m-%d, %H:%M:%S"),
                "AffectedCountries": countryNames,  # CountryNames – Country ISO2 codes,
                "NumberOfPeopleAffected": NumberOfPeopleAffected or 0,
                "InitialRequestType": InitialRequestType,
                "IFRCFocalPoint": {"Name": c_ifrc_names},
                "NSFocalPoint": {"Name": c_ns_names},
                "InitialRequestAmount": {
                    "Value": InitialRequestValue,
                    "CurrencyCode": "CHF",
                },  # Value: Field Report Appeal amount OR Field Report DREF amount (so not from Appeal table)
                # ^ CurrencyCode can be different?
            }
        }
    }

    headers = {'Content-Type': 'application/json', 'Ocp-Apim-Trace': 'true', 'Ocp-Apim-Subscription-Key': ERP_API_SUBSCRIPTION_KEY}
    # The response contains the GUID (res.text)
    res = requests.post(ERP_API_ENDPOINT, json=payload, headers=headers)

    if res.status_code == 200:
        res_text = res.text.replace('"', '')
        logger.info('Successfully posted to ERP')
        logger.info('GUID: {}'.format(res_text))
        # Saving GUID into a table so that the API can be queried with it to get info about
        # if the actual sending has failed or not.
        ERPGUID.objects.create(
            api_guid=res_text,
            field_report=data
        )

        logger.info('E-mails were sent successfully.')
    elif res.status_code == 401 or res.status_code == 403:
        logger.error(
            f'Authorization/authentication failed with status code ({res.status_code}) to the ERP API. Field Report ID: {data.id}'
        )
    else:
        logger.error(
            f'Failed to post to the ERP API with status code ({res.status_code}). Field Report ID: {data.id}'
        )
