import django.contrib.postgres.fields
from django.db import migrations, models

from eap.models import TimeFrame


class Migration(migrations.Migration):

    dependencies = [
        ("eap", "0006_remove_eapregistration_pending_pfa_at_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="keyactor",
            name="national_society",
        ),
        migrations.AlterField(
            model_name="keyactor",
            name="partner",
            field=models.CharField(help_text="Name of the partner organization or entity.", max_length=255, verbose_name="Partner"),
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="early_action_budget",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Early Actions Budget (CHF)"),
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="people_targeted",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="People Targeted."),
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="pre_positioning_budget",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Pre-positioning Budget (CHF)"),
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="readiness_budget",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Readiness Budget (CHF)"),
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="total_budget",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Total Budget (CHF)"),
        ),
        migrations.AlterField(
            model_name="plannedoperation",
            name="budget_per_sector",
            field=models.PositiveIntegerField(verbose_name="Budget per sector (CHF)"),
        ),
        migrations.AlterField(
            model_name="plannedoperation",
            name="people_targeted",
            field=models.PositiveIntegerField(verbose_name="People Targeted"),
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="early_action_budget",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Early Actions Budget (CHF)"),
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="people_targeted",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="People Targeted."),
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="pre_positioning_budget",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Pre-positioning Budget (CHF)"),
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="readiness_budget",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Readiness Budget (CHF)"),
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="total_budget",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Total Budget (CHF)"),
        ),
        migrations.AlterField(
            model_name="eapregistration",
            name="national_society_contact_title",
            field=models.CharField(default="N/A", max_length=255, verbose_name="national society contact title"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="national_society_contact_title",
            field=models.CharField(default="N/A", max_length=255, verbose_name="national society contact title"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="national_society_contact_title",
            field=models.CharField(default="N/A", max_length=255, verbose_name="national society contact title"),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_delegation_focal_point_name",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_delegation_focal_point_email",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_delegation_focal_point_title",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_delegation_focal_point_phone_number",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_head_of_delegation_name",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_head_of_delegation_email",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_head_of_delegation_title",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_head_of_delegation_phone_number",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_global_ops_coordinator_name",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_global_ops_coordinator_email",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_global_ops_coordinator_title",
        ),
        migrations.RemoveField(
            model_name="fulleap",
            name="ifrc_global_ops_coordinator_phone_number",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_delegation_focal_point_name",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_delegation_focal_point_email",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_delegation_focal_point_title",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_delegation_focal_point_phone_number",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_head_of_delegation_name",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_head_of_delegation_email",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_head_of_delegation_title",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_head_of_delegation_phone_number",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_global_ops_coordinator_name",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_global_ops_coordinator_email",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_global_ops_coordinator_title",
        ),
        migrations.RemoveField(
            model_name="simplifiedeap",
            name="ifrc_global_ops_coordinator_phone_number",
        ),
        migrations.RenameField(
            model_name="simplifiedeap",
            old_name="operational_timeframe_unit",
            new_name="activation_timeframe_unit",
        ),
        migrations.RenameField(
            model_name="simplifiedeap",
            old_name="operational_timeframe",
            new_name="activation_timeframe",
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="activation_timeframe_unit",
            field=models.IntegerField(
                blank=True,
                choices=[(10, "Years"), (20, "Months"), (30, "Days"), (40, "Hours")],
                default=20,
                null=True,
                verbose_name="Activation Timeframe Unit",
            ),
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="activation_timeframe",
            field=models.IntegerField(blank=True, null=True, verbose_name="Activation Timeframe"),
        ),
        migrations.RenameField(
            model_name="simplifiedeap",
            old_name="hazard_impact_images",
            new_name="hazard_impact_files",
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="hazard_impact_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="simplified_eap_hazard_impact_files",
                to="eap.eapfile",
                verbose_name="Hazard Impact Files",
            ),
        ),
        migrations.RenameField(
            model_name="simplifiedeap",
            old_name="risk_selected_protocols_images",
            new_name="risk_selected_protocols_files",
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="risk_selected_protocols_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="simplified_eap_risk_selected_protocols_files",
                to="eap.eapfile",
                verbose_name="Risk Selected Protocols Files",
            ),
        ),
        migrations.RenameField(
            model_name="simplifiedeap",
            old_name="selected_early_actions_images",
            new_name="selected_early_actions_files",
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="selected_early_actions_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="simplified_eap_selected_early_actions_files",
                to="eap.eapfile",
                verbose_name="Selected Early Actions Files",
            ),
        ),
        migrations.RenameField(
            model_name="simplifiedeap",
            old_name="people_targeted",
            new_name="total_people_targeted",
        ),
        migrations.AlterField(
            model_name="simplifiedeap",
            name="total_people_targeted",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Total People Targeted."),
        ),
        # --- FullEAP: _images -> _files ---
        migrations.RenameField(
            model_name="fulleap",
            old_name="hazard_selection_images",
            new_name="hazard_selection_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="hazard_selection_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="full_eap_hazard_selection_files",
                to="eap.eapfile",
                verbose_name="Hazard Files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="exposed_element_and_vulnerability_factor_images",
            new_name="exposed_element_and_vulnerability_factor_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="exposed_element_and_vulnerability_factor_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="full_eap_vulnerability_factor_files",
                to="eap.eapfile",
                verbose_name="Exposed elements and vulnerability factors files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="prioritized_impact_images",
            new_name="prioritized_impact_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="prioritized_impact_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="full_eap_prioritized_impact_files",
                to="eap.eapfile",
                verbose_name="Prioritized impact files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="forecast_selection_images",
            new_name="forecast_selection_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="forecast_selection_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="+",
                to="eap.eapfile",
                verbose_name="Forecast Selection Files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="definition_and_justification_impact_level_images",
            new_name="definition_and_justification_impact_level_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="definition_and_justification_impact_level_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="+",
                to="eap.eapfile",
                verbose_name="Definition and Justification Impact Level Files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="identification_of_the_intervention_area_images",
            new_name="identification_of_the_intervention_area_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="identification_of_the_intervention_area_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="+",
                to="eap.eapfile",
                verbose_name="Intervention Area Files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="early_action_selection_process_images",
            new_name="early_action_selection_process_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="early_action_selection_process_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="early_action_selection_process_files",
                to="eap.eapfile",
                verbose_name="Early action selection process files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="early_action_implementation_images",
            new_name="early_action_implementation_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="early_action_implementation_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="early_action_implementation_files",
                to="eap.eapfile",
                verbose_name="Early Action Implementation Files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="trigger_activation_system_images",
            new_name="trigger_activation_system_files",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="trigger_activation_system_files",
            field=models.ManyToManyField(
                blank=True,
                related_name="trigger_activation_system_files",
                to="eap.eapfile",
                verbose_name="Trigger Activation System Files",
            ),
        ),
        migrations.RenameField(
            model_name="fulleap",
            old_name="people_targeted",
            new_name="total_people_targeted",
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="total_people_targeted",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Total People Targeted."),
        ),
        migrations.AlterField(
            model_name="fulleap",
            name="lead_time",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Lead Time"),
        ),
        migrations.AlterField(
            model_name="operationactivity",
            name="timeframe",
            field=models.IntegerField(blank=True, choices=TimeFrame.choices, null=True, verbose_name="Timeframe"),
        ),
        migrations.AlterField(
            model_name="operationactivity",
            name="time_value",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.IntegerField(), blank=True, null=True, size=None, verbose_name="Activity time span"
            ),
        ),
    ]
