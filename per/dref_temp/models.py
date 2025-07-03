# per/dref_temp/models.py

from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any

@dataclass
class CountryDetails:
    iso: str
    iso3: str
    id: int
    name: str
    society_name: str
    region: int
    independent: bool = True
    record_type: int = 1
    record_type_display: str = "Country"
    is_deprecated: bool = False
    fdrs: str = ""
    average_household_size: Optional[int] = None
    translation_module_original_language: str = "en"

@dataclass
class DistrictDetails:
    name: str
    code: str
    id: int
    is_enclave: bool = False
    is_deprecated: bool = False

@dataclass
class DisasterTypeDetails:
    id: int
    name: str
    summary: str = ""
    translation_module_original_language: str = "en"

@dataclass
class UserDetails:
    id: int
    username: str
    first_name: str
    last_name: str

@dataclass
class FileDetails:
    id: int
    file: Optional[str]
    caption: Optional[str] = None
    created_by: Optional[int] = None
    client_id: Optional[str] = None
    translation_module_original_language: str = "en"
    translation_module_skip_auto_translation: bool = False
    created_by_details: Optional[UserDetails] = None

@dataclass
class NationalSocietyAction:
    id: int
    title: str
    title_display: str
    description: str
    image_url: str = ""
    translation_module_original_language: str = "en"

@dataclass
class NeedIdentified:
    id: int
    title: str
    title_display: str
    description: str
    image_url: str = ""
    translation_module_original_language: str = "en"

@dataclass
class Indicator:
    id: int
    title: str
    target: Optional[int] = None
    actual: Optional[int] = None
    translation_module_original_language: str = "en"
    translation_module_skip_auto_translation: bool = False

@dataclass
class PlannedIntervention:
    id: int
    title: str
    title_display: str
    description: str
    budget: int
    indicators: List[Indicator] = field(default_factory=list)
    person_targeted: Optional[int] = None
    person_assisted: Optional[int] = None
    male: Optional[int] = None
    female: Optional[int] = None
    image_url: str = ""
    translation_module_original_language: str = "en"
    translation_module_skip_auto_translation: bool = False
    progress_towards_outcome: Optional[str] = None
    lessons_learnt: Optional[str] = None
    narrative_description_of_achievements: Optional[str] = None
    challenges: Optional[str] = None

@dataclass
class RiskSecurity:
    id: int
    risk: str
    mitigation: str
    client_id: str = ""
    translation_module_original_language: str = "en"
    translation_module_skip_auto_translation: bool = False

@dataclass
class SourceInformation:
    id: int
    source_name: str
    source_link: str
    client_id: str = ""

@dataclass
class BaseDREF:
    """Base DREF model with common properties"""
    id: int
    title: str
    appeal_code: str
    event_date: str
    ns_respond_date: str
    created_at: str
    modified_at: str
    
    # Classifications
    type_of_onset: int
    type_of_onset_display: str
    type_of_dref: int
    type_of_dref_display: str
    disaster_category: int
    disaster_category_display: str
    status: int
    
    # Location and disaster details
    country_details: CountryDetails
    district_details: List[DistrictDetails]
    disaster_type_details: DisasterTypeDetails
    
    # People and targeting
    number_of_people_affected: int
    total_targeted_population: int
    women: int
    men: int
    girls: int
    boys: int
    disability_people_per: float
    
    # Optional fields
    glide_code: Optional[str] = None
    total_dref_allocation: Optional[int] = None
    amount_requested: Optional[int] = None
    operation_start_date: Optional[str] = None
    operation_end_date: Optional[str] = None
    total_operation_timeframe: Optional[int] = None
    
    # Contact information
    ifrc_appeal_manager_name: str = ""
    ifrc_appeal_manager_email: str = ""
    ifrc_appeal_manager_title: str = ""
    ifrc_project_manager_name: str = ""
    ifrc_project_manager_email: str = ""
    ifrc_project_manager_title: str = ""
    national_society_contact_name: str = ""
    national_society_contact_email: str = ""
    national_society_contact_title: str = ""
    
    # Response elements
    national_society_actions: List[NationalSocietyAction] = field(default_factory=list)
    needs_identified: List[NeedIdentified] = field(default_factory=list)
    planned_interventions: List[PlannedIntervention] = field(default_factory=list)
    risk_security: List[RiskSecurity] = field(default_factory=list)
    source_information: List[SourceInformation] = field(default_factory=list)
    
    # Files and media
    event_map_file: Optional[FileDetails] = None
    cover_image_file: Optional[FileDetails] = None
    images_file: List[FileDetails] = field(default_factory=list)
    
    # Metadata
    created_by_details: Optional[UserDetails] = None
    modified_by_details: Optional[UserDetails] = None
    users_details: List[UserDetails] = field(default_factory=list)
    
    # Settings
    is_published: bool = True
    translation_module_original_language: str = "en"
    translation_module_skip_auto_translation: bool = False

@dataclass
class DREFFinalReport(BaseDREF):
    """DREF Final Report"""
    financial_report_details: Optional[FileDetails] = None
    financial_report_preview: Optional[str] = None
    financial_report_description: Optional[str] = None
    num_assisted: Optional[int] = None
    assisted_num_of_women: Optional[int] = None
    assisted_num_of_men: Optional[int] = None
    main_donors: Optional[str] = None
    operation_objective: Optional[str] = None
    selection_criteria: Optional[str] = None
    national_authorities: Optional[str] = None
    partner_national_society: Optional[str] = None
    icrc: Optional[str] = None
    ifrc: Optional[str] = None
    event_description: Optional[str] = None
    event_scope: Optional[str] = None
    response_strategy: Optional[str] = None
    people_assisted: Optional[str] = None
    change_in_operational_strategy: Optional[bool] = None
    change_in_operational_strategy_text: Optional[str] = None

@dataclass
class DREFOperationalUpdate(BaseDREF):
    """DREF Operational Update"""
    operational_update_number: Optional[int] = None
    budget_file_details: Optional[FileDetails] = None
    budget_file_preview: Optional[str] = None
    dref_allocated_so_far: Optional[int] = None
    additional_allocation: Optional[int] = None
    emergency_appeal_planned: Optional[bool] = None
    new_operational_start_date: Optional[str] = None
    new_operational_end_date: Optional[str] = None
    changing_timeframe_operation: Optional[bool] = None
    changing_operation_strategy: Optional[bool] = None
    changing_target_population_of_operation: Optional[bool] = None
    changing_geographic_location: Optional[bool] = None
    changing_budget: Optional[bool] = None
    request_for_second_allocation: Optional[bool] = None
    summary_of_change: Optional[str] = None
    reporting_start_date: Optional[str] = None
    reporting_end_date: Optional[str] = None
    major_coordination_mechanism: Optional[str] = None
    partner_national_society: Optional[str] = None
    icrc: Optional[str] = None
    pmer: Optional[str] = None
    event_scope: Optional[str] = None
    selection_criteria: Optional[str] = None
    operation_objective: Optional[str] = None
    event_description: Optional[str] = None
    communication: Optional[str] = None
    logistic_capacity_of_ns: Optional[str] = None
    human_resource: Optional[str] = None
    national_authorities: Optional[str] = None
    response_strategy: Optional[str] = None
    ifrc: Optional[str] = None
    un_or_other_actor: Optional[str] = None
    anticipatory_actions: Optional[str] = None

@dataclass
class DREFBasic(BaseDREF):
    """Basic DREF"""
    budget_file_details: Optional[FileDetails] = None
    budget_file_preview: Optional[str] = None
    assessment_report_details: Optional[FileDetails] = None
    end_date: Optional[str] = None
    publishing_date: Optional[str] = None
    operation_timeframe: Optional[int] = None
    submission_to_geneva: Optional[str] = None
    date_of_approval: Optional[str] = None
    ns_request_date: Optional[str] = None
    people_in_need: Optional[int] = None
    government_requested_assistance: Optional[bool] = None
    is_there_major_coordination_mechanism: Optional[bool] = None
    complete_child_safeguarding_risk: Optional[bool] = None
    has_child_safeguarding_risk_analysis_assessment: Optional[bool] = None
    has_anti_fraud_corruption_policy: Optional[bool] = None
    has_sexual_abuse_policy: Optional[bool] = None
    has_child_protection_policy: Optional[bool] = None
    has_whistleblower_protection_policy: Optional[bool] = None
    has_anti_sexual_harassment_policy: Optional[bool] = None
    selection_criteria: Optional[str] = None
    ifrc: Optional[str] = None
    event_scope: Optional[str] = None
    identified_gaps: Optional[str] = None
    human_resource: Optional[str] = None
    operation_objective: Optional[str] = None
    pmer: Optional[str] = None
    major_coordination_mechanism: Optional[str] = None
    event_description: Optional[str] = None
    response_strategy: Optional[str] = None
    logistic_capacity_of_ns: Optional[str] = None
    national_authorities: Optional[str] = None
    communication: Optional[str] = None
    partner_national_society: Optional[str] = None
    icrc: Optional[str] = None
    un_or_other_actor: Optional[str] = None
    risk_security_concern: Optional[str] = None
    lessons_learned: Optional[str] = None
    child_safeguarding_risk_level: Optional[str] = None
    is_volunteer_team_diverse: Optional[str] = None

# Union type for all DREF types
DREFData = Union[DREFFinalReport, DREFOperationalUpdate, DREFBasic]