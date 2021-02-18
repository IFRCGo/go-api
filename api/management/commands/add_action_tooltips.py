from django.core.management.base import BaseCommand
from api.models import Action
from django.db import transaction
from django.db.models import Q
from api.logger import logger


class Command(BaseCommand):
    help = 'Adds predefined tooltip texts to Actions (most probably one-time run only)'

    @transaction.atomic
    def handle(self, *args, **options):
        tts = [
            [
                'National Society readiness',
                'Includes adapting community preparedness, response and DRR measures in view of the pandemic safety measures, especially when they are dealing with compounding disasters. Also includes adjusting contingency plans, updating Risk assessments identifying the different services that will be provided during the current disaster and how do these services fit into the National contingency plans.'
            ],
            [
                'National Society sustainability',
                'Includes identifying Core organizational budget to maintain the minimum structure of a National Society, available unrestricted reserves and unrestricted income and developing and executing business continuity plans.'
            ],
            [
                'Support to volunteers',
                'Includes providing insurance for volunteers as well as access to PPE for volunteers to safely fulfil their duties.'
            ],
            [
                'Epidemic control measures',
                'Includes testing, contact tracing and support for quarantine of contacts and isolation of COVID-19 cases not requiring clinical treatment.'
            ],
            [
                'Risk communication, community engagement, and health and hygiene promotion',
                'Includes approaches such as community-based activities, mass media (local radios, TV, press), social media outreach or face-to-face and interpersonal communication (door to door, community dialogues, community meetings) to promote hygiene and other risk reduction interventions.'
            ],
            [
                'Community-based surveillance (CBS) for COVID-19',
                'Includes staff and volunteers who have completed a training and who are actively reporting health risks through the RC/RC approach to CBS. It does not include point-of-entry screenings, call centers, active surveillance or contact tracing.'
            ],
            [
                'Infection prevention and control (IPC) and WASH (health facilities)',
                'Includes any form of infection prevention and control (IPC) support provided to health facilities. Support may include donation of personal protective equipment or medical supplies, or other medical, logistics, or coordination support, support for triage of COVID-19 cases, installation of WASH infrastructure to facilitate IPC best practices, and IPC training.'
            ],
            [
                'Infection prevention and control (IPC) and WASH (community)',
                'Includes community WASH activities such as establishing or rehabilitating a drinking water source, toilet, and/or a handwashing facility.'
            ],
            [
                'Mental health and psychosocial support services (MHPSS)',
                'Includes direct mental health and psychosocial support services to community members provided through National Society volunteers or staff.'
            ],
            [
                'Isolation and clinical case management for COVID-19 cases',
                'Includes support to health facilities that are actively treating COVID-19 cases or providing observational support and care to COVID-19 cases in isolation. Support can range from donations to staff and volunteer support.'
            ],
            [
                'Ambulance services for COVID-19 cases',
                'Includes suspected or confirmed COVID-19 patients who have received ambulance transport services by the National Society.'
            ],
            [
                'Maintain access to essential health services (community health)',
                'Includes supporting essential community health services that have been impacted/reduced as a result of COVID-19, such as community-based malaria interventions, NCD support, and immunization campaigns to counteract the reduction in community health services and/or increased need for community health services resulting from COVID-19.'
            ],
            [
                'Maintain access to essential health services (clinical and paramedical)',
                'Includes supporting health facilities supported to maintain routine essential services such as MCH, NCD, malaria treatment, and other essential services. Support can be through either physical or technical support of volunteers or staff, or support through PPE or medical supplies donation.'
            ],
            [
                'Management of the dead',
                'Includes direct burial or cremation of human remains of COVID-19 cases, and supervision of safe burial or cremation in the community.'
            ],
            [
                'Support COVID-19 Vaccination',
                'Includes activities such as service delivery, campaigns, or distribution.'
            ],
            [
                'Community engagement and accountability (CEA), including community feedback mechanisms',
                'Includes systems and approaches to collect community feedback which could mean recorded /tracked suggestions, comments, complaints, concerns, perceptions, praise, question collected through feedback systems and/or through community perception surveys.'
            ],
            [
                'Livelihoods, cash support & food aid',
                'Includes immediate food assistance or measures to protect households’ livelihoods by provisioning for lost sources of income to meet their basic needs and avoid further assets depletion. This can include all types of cash assistance to address basic needs. Also, activities for skills development such as entrepreneurship, marketing and coaching.'
            ],
            [
                'Social care and cohesion, and support to vulnerable groups',
                'Includes analysis of the specific needs of marginalized groups in the needs assessment, and/or following the PGI minimum standards and/or using equivalent guide on assessing and meeting the needs of marginalized groups.'
            ],
            [
                'Shelter and urban settlements',
                'Includes for example, household items to improve shelter conditions (clothing, bed linen, mattress, blanket, etc.), emergency shelter (tents or tool kits), accommodation in collective facilities (camps, collective centers or quarantine facilities), cash and voucher assistance to cover payment of accommodation (rent or loans), utilities and other related cost directly related with the accommodation.'
            ]
        ]

        errors = ''
        actions = Action.objects.all()
        for tip in tts:
            ac = actions.filter(Q(name__iexact=tip[0]) | Q(name_en__iexact=tip[0])).first()
            if ac:
                ac.tooltip_text_en = tip[1]
                ac.save()
            else:
                errors = errors + f'Could not find: {tip[0]}\n'

        if errors:
            logger.warn(f'Errors when adding tooltips!\n\n{errors}')
        else:
            logger.info('Successfully added all Action tooltips.')
