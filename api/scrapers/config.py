

def return_all(text):
#   return text.split(':')[0] # really the full text
    return text

# META


class MetaFields:
    glide_number = 'glideNumber'
    appeal_number = 'appealNumber'
    date_of_issue = 'dateOfIssue'
    date_of_disaster = 'dateOfDisaster'
    appeal_launch_date = 'appealLaunchDate'
    expected_time_frame = 'expectedTimeFrame'
    expected_end_date = 'expectedEndDate'
    category_allocated = 'categoryAllocated'
    dref_allocated = 'drefAllocated'
    num_of_people_affected = 'numOfPeopleAffected'
    num_of_people_to_be_assisted = 'numOfPeopleToBeAssisted'
    num_of_partner_ns_involved = 'numOfPartnerNsInvolved'
    num_of_other_partner_involved = 'numOfOtherPartnerInvolved'
    epoa_update_num = 'epoaUpdateNum'
    time_frame_covered_by_update = 'timeFrameCoveredByUpdate'
    appeal_ends = 'appealEnds'
    operation_start_date = 'operationStartDate'
    operation_end_date = 'operationEndDate'
    operation_timeframe = 'operationTimeframe'
    overall_operation_budget = 'overallOperationBudget'
    current_operation_budget = 'currentOperationBudget'

    misc = 'misc'


_mfd = MetaFields

M_KEYS = {
    _mfd.appeal_number: [
        'Emergency Appeal no', 'Emergency Appeal n°', 'Emergency Appeal n o',
        'Operation no.', 'Emergency Appeal n°', 'DREF n°', 'DREF Operation:',
        'Appeal n°',
    ],
    _mfd.glide_number: ['Glide n°:', 'Glide n°'],
    _mfd.appeal_launch_date: ['Date of launch:', 'Appeal date of launch:'],
    _mfd.date_of_issue: ['Date of issue:', 'DREF issued:', 'Issued on'],
    _mfd.date_of_disaster: ['Date of disaster:'],
    _mfd.expected_time_frame: ['Expected timeframe:'],
    _mfd.expected_end_date: ['Expected end date:'],
    _mfd.category_allocated: [
        'Category allocated to the of the disaster or crisis:',
    ],
    _mfd.dref_allocated: [
        'DREF allocated:', 'DREF allocated loan:',
    ],
    _mfd.num_of_people_affected: [
        'Total number of people affected:', 'Number of people affected:',
        'N° of people affected:',
    ],
    _mfd.num_of_people_to_be_assisted: ['Number of people to be assisted:'],
    _mfd.num_of_partner_ns_involved: [
        'Red Cross Red Crescent Movement partners actively involved in the operation:',
    ],
    _mfd.num_of_other_partner_involved: [
        'Other partner organizations actively involved in the operation:',
    ],
    _mfd.epoa_update_num: [
        'EPoA update n°', 'DREF operation update n°', 'Operations update n°',
    ],
    _mfd.time_frame_covered_by_update: [
        'Timeframe covered by this update:', 'Period covered by this update: ',
    ],
    _mfd.operation_start_date: ['Operation start date:'],
    _mfd.operation_end_date: ['Operation end date:'],
    _mfd.operation_timeframe: ['Operation timeframe:'],
    _mfd.overall_operation_budget: ['Overall operation budget:'],
    _mfd.current_operation_budget: ['Appeal budget:'],
    _mfd.appeal_ends: ['Completion date:'],

    _mfd.misc: [
        'For DREF;',
        'Start of the emergency:',
        'Emergency appeal budget 1 :',
        r'Host National Society presence \(n° of volunteers, staff, branches\):',
        'Appeal budget:',
        'Host National Society:',
        'Host National Society presence:',
        'Date of disaster:',
        'Operation manager:',
        'National Society Focal Point:',
        'Amount requested for the appeal:',
        'IFRC Project Manager \(responsible for implementation, compliances, monitoring and reporting\):', # noqa
        'Period covered by this update:',
    ],
}

M_EXTRACTORS = {
    _mfd.glide_number: return_all,
    _mfd.appeal_number: return_all,
    _mfd.appeal_launch_date: return_all,
    _mfd.date_of_issue: return_all,
    _mfd.expected_time_frame: return_all,
    _mfd.expected_end_date: return_all,
    _mfd.category_allocated: return_all,
    _mfd.dref_allocated: return_all,
    _mfd.num_of_people_affected: return_all,
    _mfd.num_of_people_to_be_assisted: return_all,
    _mfd.epoa_update_num: return_all,
    _mfd.time_frame_covered_by_update: return_all,
    _mfd.operation_start_date: return_all,
    _mfd.operation_end_date: return_all,
    _mfd.operation_timeframe: return_all,
    _mfd.date_of_disaster: return_all,
    _mfd.num_of_partner_ns_involved: return_all,
    _mfd.num_of_other_partner_involved: return_all,
    _mfd.appeal_ends: return_all,
    _mfd.overall_operation_budget: return_all,
    _mfd.current_operation_budget: return_all,
}


def get_meta_misc_keys(fields):
    """
    Return all other keys other then used by fields provided
    - fields: already used fields
    """
    misc_fields = []
    for field in M_KEYS.keys():
        if field not in fields:
            misc_fields.extend(M_KEYS[field])
    return list(set(misc_fields))

# SECTOR


class Sectors:
    health = 'health'
    shelter = 'shelter'
    livelihoods_and_basic_needs = 'livelihoodsAndBasicNeeds'
    Water_sanitation_hygiene = 'waterSanitationAndHygiene'
    disaster_Risk_reduction = 'disasterRiskReduction'
    protection_gender_inclusion = 'protectionGenderAndInclusion'
    migration = 'migration'


class SectorFields:
    male = 'male'
    female = 'female'
    requirements = 'requirements'
    people_targeted = 'peopleTargeted'
    people_reached = 'peopleReached'

    misc = 'misc'


_s = Sectors
_sfd = SectorFields


S_KEYS = {
    _s.health: ['Health'],
    _s.shelter: ['Shelter'],
    _s.livelihoods_and_basic_needs: ['Livelihoods and basic needs'],
    _s.Water_sanitation_hygiene: ['Water, sanitation and hygiene'],
    _s.disaster_Risk_reduction: ['Disaster Risk Reduction'],
    _s.protection_gender_inclusion: ['Protection, Gender and Inclusion'],
    _s.migration: ['Migration'],
}


SF_KEYS = {
    _sfd.male: ['Male:'],
    _sfd.female: ['Female:'],
    _sfd.requirements: ['Requirements'],
    _sfd.people_targeted: ['People targeted:'],
    _sfd.people_reached: ['People reached:'],

    _sfd.misc: [],
}

_SF_EXTRACTORS = {
    _sfd.male: return_all,
    _sfd.female: return_all,
    _sfd.requirements: return_all,
    _sfd.people_targeted: return_all,
    _sfd.people_reached: return_all,
}

SF_EXTRACTORS = {
    '{}__{}'.format(s_key, sf_key): _SF_EXTRACTORS.get(sf_key)
    for s_key in S_KEYS
    for sf_key in SF_KEYS
}


def get_sector_misc_keys(fields):
    """
    Return all other keys other then used by fields provided
    - fields: already used fields
    """
    misc_fields = []
    for field in M_KEYS.keys():
        if field not in fields:
            misc_fields.extend(M_KEYS[field])
    return list(set(misc_fields))
