# The many-to-many fields should be filled in with values separated by space (or be empty or use none)
import csv

from django.core.management.base import BaseCommand
from django.db import transaction

import local_units.models as models
from main.managers import BulkCreateManager


class Command(BaseCommand):
    help = "Import Health Data from CSV"
    missing_args_message = "Filename is missing. Filename / path to TAB separated CSV file required."

    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    @transaction.atomic
    def handle(self, *args, **options):

        def wash(string):
            return string.lower().replace("/", "").replace("_", "").replace(",", "").replace(" ", "")

        def wash_leave_space(string):
            return string.lower().replace("/", "").replace("_", "").replace(",", "")

        def numerize(value):
            return value if value.isdigit() else 0

        filename = options["filename"][0]
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            bulk_mgr = BulkCreateManager(chunk_size=1000)

            # Prefetch
            affiliation_id_map = {wash(name): code for code, name in models.Affiliation.objects.values_list("code", "name")}
            functionality_id_map = {wash(name): code for code, name in models.Functionality.objects.values_list("code", "name")}
            facilitytype_id_map = {wash(name): code for code, name in models.FacilityType.objects.values_list("code", "name")}
            primaryhcc_id_map = {wash(name): code for code, name in models.PrimaryHCC.objects.values_list("code", "name")}
            hospitaltype_id_map = {wash(name): code for code, name in models.HospitalType.objects.values_list("code", "name")}
            generalmedicalservice_id_map = {
                wash(name): code for code, name in models.GeneralMedicalService.objects.values_list("code", "name")
            }
            specializedmedicalservice_id_map = {
                wash(name): code for code, name in models.SpecializedMedicalService.objects.values_list("code", "name")
            }
            bloodservice_id_map = {wash(name): code for code, name in models.BloodService.objects.values_list("code", "name")}
            professionaltrainingfacility_id_map = {
                wash(name): code for code, name in models.ProfessionalTrainingFacility.objects.values_list("code", "name")
            }

            facilitytype_id_map["primaryhealthcarecentre"] = facilitytype_id_map["primaryhealthcarecenter"]
            facilitytype_id_map["residentialfacilities"] = facilitytype_id_map["residentialfacility"]
            facilitytype_id_map["trainingfacilities"] = facilitytype_id_map["trainingfacility"]
            facilitytype_id_map["hospitals"] = facilitytype_id_map["hospital"]
            facilitytype_id_map["pharmacies"] = facilitytype_id_map["pharmacy"]
            facilitytype_id_map["bloodcentres"] = facilitytype_id_map["bloodcenter"]
            facilitytype_id_map["bloodcentre"] = facilitytype_id_map["bloodcenter"]
            # facilitytype_id_map["blood"] = facilitytype_id_map["bloodcenter"]
            specializedmedicalservice_id_map["surgicalspecialties"] = specializedmedicalservice_id_map["surgicalspecialities"]

            primaryhcc_id_map[""] = None
            hospitaltype_id_map[""] = None
            generalmedicalservice_id_map[""] = None
            generalmedicalservice_id_map["none"] = None
            specializedmedicalservice_id_map[""] = None
            specializedmedicalservice_id_map["none"] = None
            bloodservice_id_map["none"] = None
            bloodservice_id_map[""] = None
            professionaltrainingfacility_id_map["none"] = None
            professionaltrainingfacility_id_map[""] = None

            for i, row in enumerate(reader, start=2):
                # Without id and affilation we can't use the row:
                if not row["DATA SOURCE ID"] or not row["Affilation"]:
                    self.stdout.write(self.style.WARNING(f"Skipping row {i + 1}: Empty id or Affilation data"))
                    continue

                # field order is the same as in the example CSV:
                f_id = row["DATA SOURCE ID"]
                f_fpe = row["Focal point email"]
                f_fpf = row["Focal point phone number"]
                f_fpp = row["Focal point position"]
                f_hft = wash(row["Health facility type"])
                f_oft = row["Other facility type"]
                f_aff = wash(row["Affilation"])
                f_fun = wash(row["Functionality"])
                f_phc = wash(row["Primary Health Care Centre"])
                f_spc = row["Speciality"]
                f_hst = wash(row["Hospital type"])
                f_ths = row["Teaching hospital"]
                f_ipc = row["In-patient Capacity"]
                f_mxc = row["Maximum Capacity"]
                f_irw = row["Isolation rooms wards"]
                f_nir = row["Number of isolation rooms"]
                f_wrh = row["Warehousing"]
                f_cch = row["Cold chain"]
                f_gms = wash_leave_space(row["General medical services"])  # m2m
                f_spm = wash_leave_space(row["Specialized medical beyond primary level"])  # m2m
                f_ots = row["Other Services"]
                f_bls = wash_leave_space(row["Blood Services"])  # m2m
                f_tnh = numerize(row["Total number of Human Resource"])
                f_gpr = numerize(row["General Practitioner"])
                f_spt = numerize(row["Specialist"])
                f_rdr = numerize(row["Residents Doctor"])
                f_nrs = numerize(row["Nurse"])
                f_dts = numerize(row["Dentist"])
                f_nur = numerize(row["Nursing Aid"])
                f_mid = numerize(row["Midwife"])
                f_omh = row["Other medical health workers"]
                f_opr = row["Other Profiles"]
                f_fbk = row["Feedback"]
                f_oaf = row["Other Affiliation"]
                f_ptf = wash_leave_space(row["Professional Training Facilities"])  # m2m
                f_ata = row["Ambulance Type A"]
                f_atb = row["Ambulance Type B"]
                f_atc = row["Ambulance Type C"]
                # not in use yet, but exists in CSV input with no data:
                # f_rlt = row["Residential long term care facilities"]

                health = models.HealthData(
                    # field order is the same as in models.py:
                    id=int(f_id),
                    affiliation_id=affiliation_id_map[f_aff],
                    other_affiliation=f_oaf or None,  # without this "or None" it gives "" when cell is empty
                    functionality_id=functionality_id_map[f_fun],
                    focal_point_email=f_fpe or None,
                    focal_point_phone_number=f_fpf or None,
                    focal_point_position=f_fpp or None,
                    health_facility_type_id=facilitytype_id_map[f_hft],
                    other_facility_type=f_oft or None,
                    primary_health_care_center_id=primaryhcc_id_map[f_phc],
                    speciality=f_spc or None,
                    hospital_type_id=hospitaltype_id_map[f_hst],
                    is_teaching_hospital=wash(f_ths) == "yes",  # boolean
                    is_in_patient_capacity=wash(f_ipc) == "yes",  # boolean
                    is_isolation_rooms_wards=wash(f_irw) == "yes",  # boolean
                    maximum_capacity=f_mxc or None,
                    number_of_isolation_rooms=f_nir or None,
                    is_warehousing=wash(f_wrh) == "yes",  # boolean
                    is_cold_chain=wash(f_cch) == "yes",  # boolean
                    ambulance_type_a=f_ata or None,
                    ambulance_type_b=f_atb or None,
                    ambulance_type_c=f_atc or None,
                    other_services=f_ots or None,
                    total_number_of_human_resource=f_tnh or None,
                    general_practitioner=f_gpr or None,
                    specialist=f_spt or None,
                    residents_doctor=f_rdr or None,
                    nurse=f_nrs or None,
                    dentist=f_dts or None,
                    nursing_aid=f_nur or None,
                    midwife=f_mid or None,
                    other_medical_heal=wash(f_omh) == "yes",  # boolean
                    other_profiles=f_opr or None,
                    feedback=f_fbk or None,
                    # Many2Many: general_medical_services: see below in a loop
                    # Many2Many: specialized_medical_beyond_primary_level: also
                    # Many2Many: blood_services: also
                    # Many2Many: professional_training_facilities: also
                )
                if f_gms:
                    for f in f_gms.split(" "):  # Can be None, so:
                        if generalmedicalservice_id_map[f]:
                            health.general_medical_services.add(generalmedicalservice_id_map[f])
                if f_spm:
                    for f in f_spm.split(" "):
                        if specializedmedicalservice_id_map[f]:
                            health.specialized_medical_beyond_primary_level.add(specializedmedicalservice_id_map[f])
                if f_bls:
                    for f in f_bls.split(" "):
                        if bloodservice_id_map[f]:
                            health.blood_services.add(bloodservice_id_map[f])
                if f_ptf:
                    for f in f_ptf.split(" "):
                        if professionaltrainingfacility_id_map[f]:
                            health.professional_training_facilities.add(professionaltrainingfacility_id_map[f])
                bulk_mgr.add(health)

            bulk_mgr.done()
            print("Bulk create summary:", bulk_mgr.summary())
