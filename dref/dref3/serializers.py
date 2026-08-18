"""Serializers for the /api/v2/dref3/ endpoint.

One flat row per DREF stage (application / operational update / final report),
sharing every field via `BaseDref3Serializer`; the three concrete subclasses
differ only in their model. Group-context values (stage label, allocation
ordinal, is_latest_stage, public) and the prefetched Appeal map are supplied
through the serializer context by `dref.dref3.common.Dref3PageHydrator`.
"""

from django.utils import timezone
from rest_framework import serializers

from api.models import Appeal
from dref.models import (
    Dref,
    DrefFinalReport,
    DrefOperationalUpdate,
    PlannedIntervention,
)

# NOTE: Proposed-action activities tag their sector from "deployments.Sector" table,
# while the exported sector columns are keyed by `PlannedIntervention.Title`.
# Sectors with no counterpart there are absent from the table and stay false.
# (multi-purpose cash, environmental sustainability, coordination and partnerships, secretariat services)
_SECTOR_ID_TO_PLANNED_INTERVENTION_TITLE = {
    # NOTE: "deployments.Sector.pk": PlannedIntervention.Title
    0: PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE,  # WASH
    1: PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION,  # PGI
    2: PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY,  # CEA
    3: PlannedIntervention.Title.MIGRATION_AND_DISPLACEMENT,  # Migration
    4: PlannedIntervention.Title.HEALTH,  # Health (public)
    5: PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY,  # DRR
    6: PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS,  # Shelter
    7: PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING,  # NS Strengthening
    8: PlannedIntervention.Title.EDUCATION,  # Education
    9: PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS,  # Livelihoods and basic needs
}


class BaseDref3Serializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    appeal_id = serializers.CharField(source="appeal_code", read_only=True)
    stage = serializers.SerializerMethodField()
    allocation = serializers.SerializerMethodField()
    pillar = serializers.SerializerMethodField()
    appeal_type = serializers.SerializerMethodField()
    allocation_type = serializers.SerializerMethodField()
    country = serializers.CharField(source="country.name_en", read_only=True)
    country_iso3 = serializers.CharField(source="country.iso3", read_only=True)
    districts = serializers.SerializerMethodField()
    district_codes = serializers.SerializerMethodField()
    region = serializers.CharField(source="country.region", read_only=True)
    disaster_definition = serializers.CharField(source="disaster_type", read_only=True)
    disaster_name = serializers.CharField(source="title", read_only=True)
    type_of_onset = serializers.SerializerMethodField()
    crisis_categorization = serializers.SerializerMethodField()
    amount_approved = serializers.SerializerMethodField()
    total_approved = serializers.SerializerMethodField()
    date_of_disaster = serializers.CharField(source="event_date", read_only=True)
    date_of_appeal_request_from_ns = serializers.SerializerMethodField()
    date_of_approval = serializers.SerializerMethodField()
    date_of_summary_publication = serializers.SerializerMethodField()
    start_date_of_operation = serializers.SerializerMethodField()
    end_date_of_operation = serializers.SerializerMethodField()
    operation_status = serializers.SerializerMethodField()
    operation_timeframe = serializers.SerializerMethodField()
    modified_at = serializers.CharField(read_only=True)
    data_origin = serializers.SerializerMethodField()
    people_affected = serializers.SerializerMethodField()
    people_targeted = serializers.SerializerMethodField()
    people_assisted = serializers.SerializerMethodField()
    population_disaggregation = serializers.SerializerMethodField()

    # Sector fields
    sector_shelter_and_basic_household_items = serializers.SerializerMethodField()
    sector_shelter_and_basic_household_items_budget = serializers.SerializerMethodField()
    sector_shelter_and_basic_household_items_people_targeted = serializers.SerializerMethodField()
    sector_shelter_and_basic_household_items_people_assisted = serializers.SerializerMethodField()
    sector_livelihoods = serializers.SerializerMethodField()
    sector_livelihoods_budget = serializers.SerializerMethodField()
    sector_livelihoods_people_targeted = serializers.SerializerMethodField()
    sector_livelihoods_people_assisted = serializers.SerializerMethodField()
    sector_multi_purpose_cash_grants = serializers.SerializerMethodField()
    sector_multi_purpose_cash_grants_budget = serializers.SerializerMethodField()
    sector_multi_purpose_cash_grants_people_targeted = serializers.SerializerMethodField()
    sector_multi_purpose_cash_grants_people_assisted = serializers.SerializerMethodField()
    sector_health = serializers.SerializerMethodField()
    sector_health_budget = serializers.SerializerMethodField()
    sector_health_people_targeted = serializers.SerializerMethodField()
    sector_health_people_assisted = serializers.SerializerMethodField()
    sector_water_sanitation_and_hygiene = serializers.SerializerMethodField()
    sector_water_sanitation_and_hygiene_budget = serializers.SerializerMethodField()
    sector_water_sanitation_and_hygiene_people_targeted = serializers.SerializerMethodField()
    sector_water_sanitation_and_hygiene_people_assisted = serializers.SerializerMethodField()
    sector_protection_gender_and_inclusion = serializers.SerializerMethodField()
    sector_protection_gender_and_inclusion_budget = serializers.SerializerMethodField()
    sector_protection_gender_and_inclusion_people_targeted = serializers.SerializerMethodField()
    sector_protection_gender_and_inclusion_people_assisted = serializers.SerializerMethodField()
    sector_education = serializers.SerializerMethodField()
    sector_education_budget = serializers.SerializerMethodField()
    sector_education_people_targeted = serializers.SerializerMethodField()
    sector_education_people_assisted = serializers.SerializerMethodField()
    sector_migration_and_displacement = serializers.SerializerMethodField()
    sector_migration_and_displacement_budget = serializers.SerializerMethodField()
    sector_migration_and_displacement_people_targeted = serializers.SerializerMethodField()
    sector_migration_and_displacement_people_assisted = serializers.SerializerMethodField()
    sector_risk_reduction_climate_adaptation_and_recovery = serializers.SerializerMethodField()
    sector_risk_reduction_climate_adaptation_and_recovery_budget = serializers.SerializerMethodField()
    sector_risk_reduction_climate_adaptation_and_recovery_people_targeted = serializers.SerializerMethodField()
    sector_risk_reduction_climate_adaptation_and_recovery_people_assisted = serializers.SerializerMethodField()
    sector_community_engagement_and_accountability = serializers.SerializerMethodField()
    sector_community_engagement_and_accountability_budget = serializers.SerializerMethodField()
    sector_community_engagement_and_accountability_people_targeted = serializers.SerializerMethodField()
    sector_community_engagement_and_accountability_people_assisted = serializers.SerializerMethodField()
    sector_environmental_sustainability = serializers.SerializerMethodField()
    sector_environmental_sustainability_budget = serializers.SerializerMethodField()
    sector_environmental_sustainability_people_targeted = serializers.SerializerMethodField()
    sector_environmental_sustainability_people_assisted = serializers.SerializerMethodField()
    sector_coordination_and_partnerships = serializers.SerializerMethodField()
    sector_coordination_and_partnerships_budget = serializers.SerializerMethodField()
    sector_coordination_and_partnerships_people_targeted = serializers.SerializerMethodField()
    sector_coordination_and_partnerships_people_assisted = serializers.SerializerMethodField()
    sector_secretariat_services = serializers.SerializerMethodField()
    sector_secretariat_services_budget = serializers.SerializerMethodField()
    sector_secretariat_services_people_targeted = serializers.SerializerMethodField()
    sector_secretariat_services_people_assisted = serializers.SerializerMethodField()
    sector_national_society_strengthening = serializers.SerializerMethodField()
    sector_national_society_strengthening_budget = serializers.SerializerMethodField()
    sector_national_society_strengthening_people_targeted = serializers.SerializerMethodField()
    sector_national_society_strengthening_people_assisted = serializers.SerializerMethodField()

    public = serializers.SerializerMethodField(read_only=True)
    is_latest_stage = serializers.SerializerMethodField(read_only=True)
    status = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    approved = serializers.SerializerMethodField()
    indicators_id = serializers.SerializerMethodField()
    link_to_emergency_page = serializers.SerializerMethodField()

    # -----------------------------
    # Per-object caches
    # -----------------------------
    def _get_cached_list(self, obj, attr_name, qs_fn):
        cache_attr = f"_{attr_name}_cache"
        if hasattr(obj, cache_attr):
            return getattr(obj, cache_attr)
        data = list(qs_fn())
        setattr(obj, cache_attr, data)
        return data

    def _planned_interventions(self, obj):
        # If prefetched, this is memory-only. If not, this is 1 query per obj.
        return self._get_cached_list(obj, "planned_interventions", lambda: obj.planned_interventions.all())

    def _proposed_actions(self, obj):
        # Only Dref and DrefFinalReport carry proposed actions.
        return self._get_cached_list(obj, "proposed_action", lambda: obj.proposed_action.all())

    def _districts_list(self, obj):
        return self._get_cached_list(obj, "districts", lambda: obj.district.all())

    def _uses_proposed_actions(self, obj):
        """Imminent-v2 rows plan their work as proposed actions rather than planned
        interventions, so their sector breakdown lives there.

        `is_dref_imminent_v2` and `proposed_action` sit on Dref and DrefFinalReport
        but not DrefOperationalUpdate, so both are checked here: a stage that gains
        the flag without the relation falls back to planned interventions instead of
        failing on every row.
        """
        return (
            obj.type_of_dref == Dref.DrefType.IMMINENT
            and getattr(obj, "is_dref_imminent_v2", False)
            and hasattr(type(obj), "proposed_action")
        )

    def _proposed_action_sector_index(self, obj):
        """Proposed actions budget per action (early action / early response), not per
        sector, and record no people numbers, so only the sector flag is available."""
        idx = {}
        for action in self._proposed_actions(obj):
            for activity in action.activities.all():
                title = _SECTOR_ID_TO_PLANNED_INTERVENTION_TITLE.get(activity.sector_id)
                if title is not None:
                    idx[title] = {"any": True}
        return idx

    def _sector_index(self, obj):
        """
        One pass per object.
        PlannedIntervention.title -> {"any": bool, "budget": number, "people_targeted": number, "people_assisted": number}
        Imminent-v2 rows carry only {"any": True}; the remaining keys read as null.
        """
        cache_attr = "_sector_index_cache"
        if hasattr(obj, cache_attr):
            return getattr(obj, cache_attr)

        if self._uses_proposed_actions(obj):
            idx = self._proposed_action_sector_index(obj)
            setattr(obj, cache_attr, idx)
            return idx

        idx = {}
        for p in self._planned_interventions(obj):
            t = p.title
            rec = idx.setdefault(t, {"any": False, "budget": 0, "people_targeted": 0, "people_assisted": 0})
            rec["any"] = True
            rec["budget"] += p.budget or 0
            rec["people_targeted"] += p.person_targeted or 0
            # FIXME: a declared sector with no recorded number serializes as 0, not null (the
            # `or 0` above), so "not reported" is indistinguishable from "genuinely zero". Kept
            # for consistency with budget/people_targeted, but it bites people_assisted hardest:
            # PlannedIntervention.person_assisted is only ever filled in at final-report stage,
            # so every application row and nearly every operational-update row reports 0 people
            # assisted rather than null. Confirm with the data consumer whether these should be
            # null before final-report stage; if so, seed these keys None and add with
            # `(rec[key] or 0) + (value or 0)`.
            rec["people_assisted"] += p.person_assisted or 0

        setattr(obj, cache_attr, idx)
        return idx

    def _sector_any(self, obj, topic):
        return self._sector_index(obj).get(topic, {}).get("any", False)

    def _sector_budget(self, obj, topic):
        return self._sector_index(obj).get(topic, {}).get("budget", None)

    def _sector_people_targeted(self, obj, topic):
        return self._sector_index(obj).get(topic, {}).get("people_targeted", None)

    def _sector_people_assisted(self, obj, topic):
        return self._sector_index(obj).get(topic, {}).get("people_assisted", None)

    def _appeal_cache(self):
        if not hasattr(self, "_appeal_by_code"):
            self._appeal_by_code = {}
        return self._appeal_by_code

    # -----------------------------
    # Context-driven fields
    # -----------------------------
    def get_public(self, obj):
        return self.context.get("public")

    def get_is_latest_stage(self, obj):
        return self.context.get("is_latest_stage")

    def get_stage(self, obj):
        return self.context.get("stage")

    def get_allocation(self, obj):
        return self.context.get("allocation")

    # -----------------------------
    # Simple computed fields
    # -----------------------------
    def get_id(self, obj):
        return f"{type(obj).__name__}-{obj.id}"

    def get_pillar(self, obj):
        return "Anticipatory" if obj.type_of_dref == Dref.DrefType.IMMINENT else "Response"

    def get_appeal_type(self, obj):
        if obj.type_of_dref == Dref.DrefType.IMMINENT:
            return "i-DREF"
        elif obj.type_of_dref == Dref.DrefType.LOAN:
            return "EA"
        return "DREF"

    def get_allocation_type(self, obj):
        return "Loan" if obj.type_of_dref == Dref.DrefType.LOAN else "Grant"

    def get_districts(self, obj):
        return ", ".join(d.name for d in self._districts_list(obj))

    def get_district_codes(self, obj):
        return ", ".join(d.code for d in self._districts_list(obj))

    def get_type_of_onset(self, obj):
        type_of_onset = obj.type_of_onset if obj.type_of_onset != 0 else 1
        return Dref.OnsetType(type_of_onset).label

    def get_crisis_categorization(self, obj):
        if hasattr(obj, "disaster_category") and obj.disaster_category is not None:
            return Dref.DisasterCategory(obj.disaster_category).label
        return "Yellow (?)"

    def get_amount_approved(self, obj):
        if hasattr(obj, "amount_requested"):
            return obj.amount_requested
        if hasattr(obj, "additional_allocation"):
            return obj.additional_allocation
        return 0

    def get_total_approved(self, obj):
        if hasattr(obj, "total_dref_allocation"):
            return obj.total_dref_allocation
        if hasattr(obj, "amount_requested"):
            return obj.amount_requested
        return 0

    def get_date_of_appeal_request_from_ns(self, obj):
        if type(obj).__name__ == "Dref" and hasattr(obj, "ns_request_date"):
            return obj.ns_request_date

    def get_date_of_approval(self, obj):
        if hasattr(obj, "date_of_approval"):
            return obj.date_of_approval

    def get_date_of_summary_publication(self, obj):
        if type(obj).__name__ == "Dref" and hasattr(obj, "publishing_date"):
            return obj.publishing_date

    def get_start_date_of_operation(self, obj):
        if hasattr(obj, "event_date"):
            return obj.event_date

    def get_end_date_of_operation(self, obj):
        t = type(obj).__name__
        if t == "Dref" and hasattr(obj, "end_date"):
            return obj.end_date
        if t == "DrefOperationalUpdate" and hasattr(obj, "new_operational_end_date"):
            return obj.new_operational_end_date
        if t == "DrefFinalReport" and hasattr(obj, "operation_end_date"):
            return obj.operation_end_date

    def get_operation_status(self, obj):
        start = self.get_start_date_of_operation(obj)
        end = self.get_end_date_of_operation(obj)
        if not start or not end:
            return None
        try:
            today = timezone.now().date()
            if hasattr(start, "date") and callable(getattr(start, "date")):
                start = start.date()
            if hasattr(end, "date") and callable(getattr(end, "date")):
                end = end.date()
            return "active" if start <= today <= end else "closed"
        except Exception:
            return None

    def get_operation_timeframe(self, obj):
        t = type(obj).__name__
        if t == "Dref" and hasattr(obj, "operation_timeframe"):
            return obj.operation_timeframe
        if t != "Dref" and hasattr(obj, "total_operation_timeframe"):
            return obj.total_operation_timeframe

    def get_data_origin(self, obj):
        return "DREF process in GO"

    def get_people_affected(self, obj):
        t = type(obj).__name__
        if t == "Dref" and hasattr(obj, "num_affected"):
            return obj.num_affected
        if t != "Dref" and hasattr(obj, "number_of_people_affected"):
            return obj.number_of_people_affected

    def get_people_targeted(self, obj):
        t = type(obj).__name__
        if t != "DrefOperationalUpdate" and hasattr(obj, "total_targeted_population"):
            return obj.total_targeted_population
        if t == "DrefOperationalUpdate" and hasattr(obj, "number_of_people_targeted"):
            return obj.number_of_people_targeted

    def get_people_assisted(self, obj):
        if type(obj).__name__ == "DrefFinalReport":
            return obj.num_assisted

    def get_population_disaggregation(self, obj):
        """Return population disaggregation dict.

        Structure:
        {
            "Women": women,
            "Girls (under 18)": girls,
            "Men": men,
            "Boys (under 18)": boys,
            "Rural": "people_per_local%",
            "Urban": "people_per_urban%"
        }
        Only include keys that have a non-None underlying value.
        Percentages are suffixed with % if numeric.
        """
        women = getattr(obj, "women", None)
        girls = getattr(obj, "girls", None)
        men = getattr(obj, "men", None)
        boys = getattr(obj, "boys", None)
        urban = getattr(obj, "people_per_urban", None)
        rural = getattr(obj, "people_per_local", None)

        def pct(val):
            if val is None:
                return None
            try:
                return f"{int(val)}%"
            except (ValueError, TypeError):
                return None

        data = {}
        if women is not None:
            data["Women"] = women
        if girls is not None:
            data["Girls (under 18)"] = girls
        if men is not None:
            data["Men"] = men
        if boys is not None:
            data["Boys (under 18)"] = boys
        if rural is not None:
            rural_pct = pct(rural)
            if rural_pct is not None:
                data["Rural"] = rural_pct
        if urban is not None:
            urban_pct = pct(urban)
            if urban_pct is not None:
                data["Urban"] = urban_pct

        return data or None

    # -----------------------------
    # Sector fields (O(1) lookups after one pass)
    # -----------------------------
    def get_sector_shelter_and_basic_household_items(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS)

    def get_sector_shelter_and_basic_household_items_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS)

    def get_sector_shelter_and_basic_household_items_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS)

    def get_sector_shelter_and_basic_household_items_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.SHELTER_HOUSING_AND_SETTLEMENTS)

    def get_sector_livelihoods(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS)

    def get_sector_livelihoods_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS)

    def get_sector_livelihoods_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS)

    def get_sector_livelihoods_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.LIVELIHOODS_AND_BASIC_NEEDS)

    def get_sector_multi_purpose_cash_grants(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.MULTI_PURPOSE_CASH)

    def get_sector_multi_purpose_cash_grants_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.MULTI_PURPOSE_CASH)

    def get_sector_multi_purpose_cash_grants_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.MULTI_PURPOSE_CASH)

    def get_sector_multi_purpose_cash_grants_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.MULTI_PURPOSE_CASH)

    def get_sector_health(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.HEALTH)

    def get_sector_health_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.HEALTH)

    def get_sector_health_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.HEALTH)

    def get_sector_health_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.HEALTH)

    def get_sector_water_sanitation_and_hygiene(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE)

    def get_sector_water_sanitation_and_hygiene_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE)

    def get_sector_water_sanitation_and_hygiene_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE)

    def get_sector_water_sanitation_and_hygiene_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.WATER_SANITATION_AND_HYGIENE)

    def get_sector_protection_gender_and_inclusion(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION)

    def get_sector_protection_gender_and_inclusion_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION)

    def get_sector_protection_gender_and_inclusion_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION)

    def get_sector_protection_gender_and_inclusion_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.PROTECTION_GENDER_AND_INCLUSION)

    def get_sector_education(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.EDUCATION)

    def get_sector_education_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.EDUCATION)

    def get_sector_education_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.EDUCATION)

    def get_sector_education_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.EDUCATION)

    def get_sector_migration_and_displacement(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.MIGRATION_AND_DISPLACEMENT)

    def get_sector_migration_and_displacement_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.MIGRATION_AND_DISPLACEMENT)

    def get_sector_migration_and_displacement_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.MIGRATION_AND_DISPLACEMENT)

    def get_sector_migration_and_displacement_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.MIGRATION_AND_DISPLACEMENT)

    def get_sector_risk_reduction_climate_adaptation_and_recovery(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY)

    def get_sector_risk_reduction_climate_adaptation_and_recovery_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY)

    def get_sector_risk_reduction_climate_adaptation_and_recovery_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY)

    def get_sector_risk_reduction_climate_adaptation_and_recovery_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.RISK_REDUCTION_CLIMATE_ADAPTATION_AND_RECOVERY)

    def get_sector_community_engagement_and_accountability(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY)

    def get_sector_community_engagement_and_accountability_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY)

    def get_sector_community_engagement_and_accountability_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY)

    def get_sector_community_engagement_and_accountability_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.COMMUNITY_ENGAGEMENT_AND_ACCOUNTABILITY)

    def get_sector_environmental_sustainability(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY)

    def get_sector_environmental_sustainability_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY)

    def get_sector_environmental_sustainability_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY)

    def get_sector_environmental_sustainability_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.ENVIRONMENTAL_SUSTAINABILITY)

    def get_sector_coordination_and_partnerships(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.COORDINATION_AND_PARTNERSHIPS)

    def get_sector_coordination_and_partnerships_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.COORDINATION_AND_PARTNERSHIPS)

    def get_sector_coordination_and_partnerships_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.COORDINATION_AND_PARTNERSHIPS)

    def get_sector_coordination_and_partnerships_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.COORDINATION_AND_PARTNERSHIPS)

    def get_sector_secretariat_services(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.SECRETARIAT_SERVICES)

    def get_sector_secretariat_services_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.SECRETARIAT_SERVICES)

    def get_sector_secretariat_services_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.SECRETARIAT_SERVICES)

    def get_sector_secretariat_services_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.SECRETARIAT_SERVICES)

    def get_sector_national_society_strengthening(self, obj):
        return self._sector_any(obj, PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING)

    def get_sector_national_society_strengthening_budget(self, obj):
        return self._sector_budget(obj, PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING)

    def get_sector_national_society_strengthening_people_targeted(self, obj):
        return self._sector_people_targeted(obj, PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING)

    def get_sector_national_society_strengthening_people_assisted(self, obj):
        return self._sector_people_assisted(obj, PlannedIntervention.Title.NATIONAL_SOCIETY_STRENGTHENING)

    # -----------------------------
    # Other method fields
    # -----------------------------
    def get_approved(self, obj):
        return True if obj.status == Dref.Status.APPROVED else False

    def get_indicators_id(self, obj):
        return None

    def get_link_to_emergency_page(self, obj):
        code = getattr(obj, "appeal_code", None)
        if not code:
            return None

        cache = self._appeal_cache()
        if code in cache:
            appeal = cache[code]
        else:
            prefetched = self.context.get("prefetched_appeal_by_code")
            if prefetched is not None:
                # Prefetched for the whole page: a miss means no Appeal exists,
                # so don't fall back to a per-row query (N+1).
                appeal = prefetched.get(code)
            else:
                try:
                    appeal = Appeal.objects.only("event_id").get(code=code)
                except Appeal.DoesNotExist:
                    appeal = None
            cache[code] = appeal

        if not appeal or not getattr(appeal, "event_id", None):
            return None
        return f"https://go.ifrc.org/emergencies/{appeal.event_id}/details"

    class Meta:
        abstract = True
        fields = [
            "id",
            "appeal_id",
            "stage",
            "allocation",
            "pillar",
            "appeal_type",
            "allocation_type",
            "country",
            "country_iso3",
            "districts",
            "district_codes",
            "region",
            "disaster_definition",
            "disaster_name",
            "type_of_onset",
            "crisis_categorization",
            "amount_approved",
            "total_approved",
            "date_of_disaster",
            "date_of_appeal_request_from_ns",
            "date_of_approval",
            "date_of_summary_publication",
            "start_date_of_operation",
            "end_date_of_operation",
            "operation_status",
            "operation_timeframe",
            "modified_at",
            "data_origin",
            "people_affected",
            "people_targeted",
            "people_assisted",
            "population_disaggregation",
            "sector_shelter_and_basic_household_items",
            "sector_shelter_and_basic_household_items_budget",
            "sector_shelter_and_basic_household_items_people_targeted",
            "sector_shelter_and_basic_household_items_people_assisted",
            "sector_livelihoods",
            "sector_livelihoods_budget",
            "sector_livelihoods_people_targeted",
            "sector_livelihoods_people_assisted",
            "sector_multi_purpose_cash_grants",
            "sector_multi_purpose_cash_grants_budget",
            "sector_multi_purpose_cash_grants_people_targeted",
            "sector_multi_purpose_cash_grants_people_assisted",
            "sector_health",
            "sector_health_budget",
            "sector_health_people_targeted",
            "sector_health_people_assisted",
            "sector_water_sanitation_and_hygiene",
            "sector_water_sanitation_and_hygiene_budget",
            "sector_water_sanitation_and_hygiene_people_targeted",
            "sector_water_sanitation_and_hygiene_people_assisted",
            "sector_protection_gender_and_inclusion",
            "sector_protection_gender_and_inclusion_budget",
            "sector_protection_gender_and_inclusion_people_targeted",
            "sector_protection_gender_and_inclusion_people_assisted",
            "sector_education",
            "sector_education_budget",
            "sector_education_people_targeted",
            "sector_education_people_assisted",
            "sector_migration_and_displacement",
            "sector_migration_and_displacement_budget",
            "sector_migration_and_displacement_people_targeted",
            "sector_migration_and_displacement_people_assisted",
            "sector_risk_reduction_climate_adaptation_and_recovery",
            "sector_risk_reduction_climate_adaptation_and_recovery_budget",
            "sector_risk_reduction_climate_adaptation_and_recovery_people_targeted",
            "sector_risk_reduction_climate_adaptation_and_recovery_people_assisted",
            "sector_community_engagement_and_accountability",
            "sector_community_engagement_and_accountability_budget",
            "sector_community_engagement_and_accountability_people_targeted",
            "sector_community_engagement_and_accountability_people_assisted",
            "sector_environmental_sustainability",
            "sector_environmental_sustainability_budget",
            "sector_environmental_sustainability_people_targeted",
            "sector_environmental_sustainability_people_assisted",
            "sector_coordination_and_partnerships",
            "sector_coordination_and_partnerships_budget",
            "sector_coordination_and_partnerships_people_targeted",
            "sector_coordination_and_partnerships_people_assisted",
            "sector_secretariat_services",
            "sector_secretariat_services_budget",
            "sector_secretariat_services_people_targeted",
            "sector_secretariat_services_people_assisted",
            "sector_national_society_strengthening",
            "sector_national_society_strengthening_budget",
            "sector_national_society_strengthening_people_targeted",
            "sector_national_society_strengthening_people_assisted",
            "public",
            "is_latest_stage",
            "status",
            "status_display",
            "approved",
            "indicators_id",
            "link_to_emergency_page",
        ]


class Dref3Serializer(BaseDref3Serializer):
    class Meta(BaseDref3Serializer.Meta):
        model = Dref


class DrefOperationalUpdate3Serializer(BaseDref3Serializer):
    class Meta(BaseDref3Serializer.Meta):
        model = DrefOperationalUpdate


class DrefFinalReport3Serializer(BaseDref3Serializer):
    class Meta(BaseDref3Serializer.Meta):
        model = DrefFinalReport
