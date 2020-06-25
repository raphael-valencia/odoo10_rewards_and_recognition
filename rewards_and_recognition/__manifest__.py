# -*- coding: utf-8 -*-
{
    "name": "Rewards and Recognition System",
    "summary": """
        Manage rewards and recognition processes and data""",
    "description": """
        - Track employee rewards and recognition information
        - Implement rewards and recognition workflows
        - Manage medrewards and recognition data
    """,
    "category": "Rewards and Recognition",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "hr_201", "hr_attendance", "hr_credits", "target"],
    # always loaded
    "data": [
        # DATA
        "data/module_category.xml",
        "data/award_category.xml",
        "data/award.xml",
        "data/mey_assessment_criteria.xml",
        "data/cron.xml",
        # SECURITY
        "security/groups.xml",
        "security/rules.xml",
        "security/ir.model.access.csv",
        # WIZARDS
        "wizards/awardee_action_wizard.xml",
        "wizards/awardee_batch_report_wizard.xml",
        # VIEWS
        "views/award_views.xml",
        "views/mey_assessment_criteria_views.xml",
        "views/mey_interview_assessment_views.xml",
        "views/mey_committee_views.xml",
        "views/awardee_views.xml",
        "views/awardee_batch_views.xml",
        "views/inherited_hr_employee_views.xml",
        "views/inherited_personal_data_sheet_views.xml",
        # REPORT VIEWS
        "report_views/mey_scoresheet_report_template.xml",
        "report_views/loyalty_awardees_report_template.xml",
        "report_views/career_report_template.xml",
        "report_views/pbb_eval_summary_report_template.xml",
        "report_views/pbb_delivery_units_report_template.xml",
        "report_views/pbb_all_departments_report_template.xml",
        "report_views/pbb_per_department_report_template.xml",
        "report_views/qualified_mey_nominees_report_template.xml",
        "report_views/for_posting_mey_nominees_report_template.xml",
        "report_views/mey_interview_schedule_report_template.xml",
        "report_views/report_views.xml",
        # MENU ITEM VIEW
        "views/_menuitems.xml",
    ],
    "application": True,
}
