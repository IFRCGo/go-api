import requests
import base64
import pytz
from datetime import datetime
from api.models import RequestChoices, ERPGUID
from api.logger import logger
from django.conf import settings


# FIXME: this
ERP_API_ENDPOINT = settings.ERP_API_ENDPOINT


def log_errors(errors):
    if len(errors):
        logger.error('Produced the following errors:')
        logger.error('[%s]' % ', '.join(map(str, errors)))


def push_fr_data(data, retired='No'):
    # Contacts
    c_ifrc = data.contacts.filter(ctype__iexact='Federation')
    c_ns = data.contacts.filter(ctype__iexact='NationalSociety')

    # Encode with base64 into bytes, then converting it back to strings for the JSON
    # TODO: check date formats and such when testing...
    try:
        requestTitle = data.event.name # Emergency name
    except AttributeError:
        requestTitle = '-'

    try:
        countryNames = ";".join(country.iso for country in data.event.countries.all()) # Country ISO2 codes, ; separated
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

    payload0 = {
    "Emergency": {
            "EmergencyId": data.event_id,  # Emergency ID, RequestId
            "EmergencyTitle": requestTitle,  # Emergency name, RequestTitle
            "DisasterStartDate": disasterStartDate.strftime("%Y-%m-%d, %H:%M:%S"),  # Emergency DisasterStartDate
            "DisasterTypeId": data.dtype_id,  # dtype ID
            "DataAreaId": "ifrc",
            "FieldReport": {
                "RequestRetired": retired,  # Not sure if this will be needed/used at all
                "FieldReportId": data.id,  # Field Report ID, GORequestId
                "ReportedDateTime":  data.updated_at.strftime("%Y-%m-%d, %H:%M:%S"),  # Field Report Updated at !!!FIXME!!!
                "RequestCreationDate": data.created_at.strftime("%Y-%m-%d, %H:%M:%S"),
                "AffectedCountries": countryNames,  # CountryNames – Country ISO2 codes,
                "NumberOfPeopleAffected": data.num_affected,
                "InitialRequestType": "EA" if data.appeal != RequestChoices.NO else ("DREF" if data.dref != RequestChoices.NO else ""),
                "IFRCFocalPoint": ",".join(con.name for con in c_ifrc),
                "NSFocalPoint": ",".join(con.name for con in c_ns),
                "InitialRequestAmount": data.appeal_amount,  # Field Report Appeal amount
            }
        }
    }

    payload = {
        "Emergency": {
            "EmergencyId": "EM-6424247",
            "EmergencyTitle": "Internal Demo crizis",
            "DisasterStartDate": "2020-10-17",
            "DisasterTypeId": "Complex Emergency",
            "DataAreaId": "ifrc",
            "FieldReport": {
                "RequestRetired": False,
                "FieldReportId": "420007",
                "ReportedDateTime": "2021-01-07",
                "RequestCreationDate": "2021-01-07",
                "AffectedCountries": [
                    "AR",
                    "BI",
                    "CL"
                ],
                "NumberOfPeopleAffected": 30000,
                "InitialRequestType": "EA",
                "IFRCFocalPoint": {
                    "Name": "Jane Doe"
                },
                "NSFocalPoint": {
                    "Name": "Hane Doe"
                },
                "InitialRequestAmount": {
                    "Value": 12345678.00,
                    "CurrencyCode": "CHF"
                }
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
