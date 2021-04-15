import requests
import base64
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
    payload = {
        "RequestId": data.event_id,  # Emergency ID
        "GORequestId": data.id,  # Field Report ID
        "RequestTitle": data.event.name,  # Emergency name
        "CountryNames": ";".join(country.iso for country in data.event.countries),  # Country ISO2 codes, ; separated
        "DisasterTypeId": data.dtype_id,  # dtype ID
        "NSRequestDate": data.created_at,
        "NumberOfPeopleAffected": data.num_affected,
        "DisasterStartDate": data.event.disaster_start_date,  # Emergency DisasterStartDate
        '''
            If “Appeal” <> “No”, then “EA”.
            Else if “DREF” = “No”, then “DREF”
            Else “Empty”
            (if both DREF and Appeal, then the type must be EA)
        '''
        "InitialRequestType": "EA" if data.appeal != RequestChoices.NO else ("DREF" if data.dref != RequestChoices.NO else ""),
        "IFRCFocalPoint": ",".join(con.name for con in c_ifrc),
        "NSFocalPoint": ",".join(con.name for con in c_ns),
        "InitialRequestAmount": data.appeal_amount,  # Field Report Appeal amount
        "Retired": retired,  # Not sure if this will be needed/used at all
        "UpdatedDateTime": data.updated_at  # Field Report Updated at
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
