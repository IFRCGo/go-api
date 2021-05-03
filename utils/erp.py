import requests
import base64
import pytz
from datetime import datetime
from api.models import RequestChoices, ERPGUID
from api.logger import logger
from django.conf import settings


ERP_API_ENDPOINT = settings.ERP_API_ENDPOINT


def push_fr_data(data, retired=False):
    # Contacts
    c_ifrc_names = ",".join(data.contacts.filter(ctype__iexact='Federation').values_list('name', flat=True))  # normally there is only 1
    c_ns_names = ",".join(data.contacts.filter(ctype__iexact='NationalSociety').values_list('name', flat=True))  # normally there is only 1

    requestTitle = data.event.name if data.event else '-'  # Emergency name

    try:
        countryNames = [country.iso for country in data.event.countries.all()] # Country ISO2 codes in emergency
        countryNames += [country.iso for country in data.countries.all()] # Country ISO2 codes in field report
    except AttributeError:
        countryNames = '[]'

    try:
        disasterStartDate = data.event.disaster_start_date  # Emergency DisasterStartDate
    except AttributeError:
        disasterStartDate = pytz.timezone("UTC").localize(datetime(1900, 1, 1, 1, 1, 1, 1))

        '''
        InitialRequestType:
            If “Appeal” <> “No”, then “EA”.
            Else if “DREF” = “No”, then “DREF”
            Else “Empty”
            (if both DREF and Appeal, then the type must be EA)
        '''

    payload = {
    "Emergency": {
            "EmergencyId": 0 if data.event_id is None else data.event_id,  # Emergency ID, RequestId
            "EmergencyTitle": requestTitle,  # Emergency name, RequestTitle
            "DisasterStartDate": disasterStartDate.strftime("%Y-%m-%d, %H:%M:%S"),  # Emergency DisasterStartDate
            "DisasterTypeId": data.dtype.name,  # dtype name. Not dtype_id!
            "DataAreaId": "ifrc",
            "FieldReport": {
                "RequestRetired": retired,  # Not sure if this will be needed/used at all
                "FieldReportId": data.id,  # Field Report ID, GORequestId
                "ReportedDateTime":  data.updated_at.strftime("%Y-%m-%d, %H:%M:%S"),  # Field Report Updated at !!!FIXME!!!
                "RequestCreationDate": data.created_at.strftime("%Y-%m-%d, %H:%M:%S"),
                "AffectedCountries": countryNames,  # CountryNames – Country ISO2 codes,
                "NumberOfPeopleAffected": 0 if data.num_affected is None else data.num_affected,
                "InitialRequestType": "EA" if data.appeal != RequestChoices.NO else ("DREF" if data.dref != RequestChoices.NO else "Empty"),
                "IFRCFocalPoint": {"Name": c_ifrc_names},
                "NSFocalPoint": {"Name": c_ns_names},
                "InitialRequestAmount": {"Value": 0 if data.appeal_amount is None else data.appeal_amount, "CurrencyCode": "CHF"}  # Field Report Appeal amount
                # ^ CurrencyCode can be different?
            }
        }
    }

    # The response contains the GUID (res.text)
    res = requests.post(ERP_API_ENDPOINT, json=payload)
    res_text = res.text.replace('"', '')

    if res.status_code == 200:
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
