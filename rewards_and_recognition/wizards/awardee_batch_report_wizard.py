from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AwardeeBatchReportWizard(models.TransientModel):
    """
    Awardee Batch Report Wizard that appears upon clicking 'Awardee Batch Report'
    from Report menu item
    """

    _name = "rewards.awardee_batch_report_wizard"
    _description = "Awardee Batch Report Wizard"

    MEY = "mey"
    LOYALTY = "loyalty"
    PBB = "pbb"
    CAREER = "career"

    INTERVIEW = "interview"
    POSTING = "posting"
    QUALIFIED = "qualified"
    PROPOSED = "proposed"

    SUMMARY = "summary"
    DELIVERY_UNITS = "delivery_units"
    ALL_DEPARTMENTS = "all_departments"
    PER_DEPARTMENT = "per_department"

    AWARD_TYPES = ((MEY, "MEY"), (LOYALTY, "Loyalty"), (PBB, "PBB"), (CAREER, "Career"))

    MEY_REPORT_TYPES = (
        (INTERVIEW, "MEY Schedule of Interviews"),
        (POSTING, "For Posting MEY Nominees"),
        (QUALIFIED, "List of Qualified MEY Nominees"),
        (PROPOSED, "Proposed Schedule of Interviews"),
    )

    PBB_REPORT_TYPES = (
        (SUMMARY, "Evaluation Matrix Summary"),
        (DELIVERY_UNITS, "Ranking of Delivery Units"),
        (
            ALL_DEPARTMENTS,
            "List of Active Employees Qualified to Receive PBB (All Departments)",
        ),
        (
            PER_DEPARTMENT,
            (
                "Summary of Performance Rating of Permanent and Casual Employees (Per Department)"
            ),
        ),
    )

    awardee_batch_id = fields.Many2one(
        comodel_name="rewards.awardee_batch",
        string="Awardee Batch",
        required=True,
        domain=[("state", "=", "done")],
    )
    award_type = fields.Selection(
        selection=AWARD_TYPES, compute="_compute_award_type", store=True
    )
    """
    CAREER Fields
    """
    date_from = fields.Date()
    date_to = fields.Date()
    """
    MEY Fields
    """
    committee_member = fields.Many2one(comodel_name="rewards.mey_committee")
    mey_report_type = fields.Selection(
        string="MEY Report Type", selection=MEY_REPORT_TYPES
    )
    preliminaries_date_from = fields.Datetime()
    preliminaries_date_to = fields.Datetime()
    deliberation_date = fields.Datetime()
    """
    PBB Fields
    """
    pbb_report_type = fields.Selection(
        string="PBB Report Type", selection=PBB_REPORT_TYPES
    )
    employee_no_pbb_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="hr_employee_no_pbb_rel",
        string="Did not meet Targets (No PBB)",
    )
    employee_no_saln_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="hr_employee_no_saln_rel",
        string="Did not submit SALN",
    )
    employee_no_ca_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="hr_employee_no_ca_rel",
        string="Did not liquidate Cash Advance within reglementary period",
    )
    employee_no_spms_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="hr_employee_no_spms_rel",
        string="Did not submit SPMS Forms",
    )
    employee_excluded_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="hr_employee_excluded_rel",
        string="Excluded due to other reasons \
            (i.e Responsible for not submitting APP, APCPI or others)",
    )
    """
    General Fields
    """
    prepared_by_id = fields.Many2one(
        comodel_name="hr.employee", default=lambda self: self.env.user.employee_ids.id,
    )
    checked_by_id = fields.Many2one(
        comodel_name="hr.employee",
        domain=lambda self: self.env["hr.department"].get_hr_employees(),
    )
    noted_by_id = fields.Many2one(
        comodel_name="hr.employee",
        domain=lambda self: self.env["hr.department"].get_hr_employees(),
    )

    @api.multi
    def action_print_report(self):
        """
        Print report base on award type
        """
        data = {"form": {"awardee_batch_id": self.awardee_batch_id.id,}}
        if self.award_type == self.CAREER:
            data["form"].update(
                {
                    "date_from": self.date_from,
                    "date_to": self.date_to,
                    "prepared_by_id": self.prepared_by_id.id,
                    "checked_by_id": self.checked_by_id.id,
                    "noted_by_id": self.noted_by_id.id,
                }
            )
            report_id = self.env.ref("rewards.report_career")
        elif self.award_type == self.PBB:
            if self.pbb_report_type == self.SUMMARY:
                report_id = self.env.ref("rewards.report_pbb_eval_summary")
            elif self.pbb_report_type == self.DELIVERY_UNITS:
                data["form"].update(
                    {
                        "employee_no_pbb_ids": self.employee_no_pbb_ids.ids,
                        "employee_no_saln_ids": self.employee_no_saln_ids.ids,
                        "employee_no_ca_ids": self.employee_no_ca_ids.ids,
                        "employee_no_spms_ids": self.employee_no_spms_ids.ids,
                        "employee_excluded_ids": self.employee_excluded_ids.ids,
                    }
                )
                report_id = self.env.ref("rewards.report_pbb_delivery_units")
            elif self.pbb_report_type == self.ALL_DEPARTMENTS:
                data["form"].update(
                    {
                        "prepared_by_id": self.prepared_by_id.id,
                        "checked_by_id": self.checked_by_id.id,
                        "noted_by_id": self.noted_by_id.id,
                    }
                )
                report_id = self.env.ref("rewards.report_pbb_all_departments")
            elif self.pbb_report_type == self.PER_DEPARTMENT:
                report_id = self.env.ref("rewards.report_pbb_per_department")
        elif self.award_type == self.LOYALTY:
            report_id = self.env.ref("rewards.report_loyalty_awardees")
        elif self.award_type == self.MEY:
            data["form"].update({"committee_member_id": self.committee_member.id})
            if self.mey_report_type == self.QUALIFIED:
                report_id = self.env.ref("rewards.report_qualified_mey_nominees")
            elif self.mey_report_type == self.POSTING:
                report_id = self.env.ref("rewards.report_for_posting_mey_nominees")
            elif self.mey_report_type == self.INTERVIEW:
                report_id = self.env.ref("rewards.report_mey_interview_schedule")
            elif self.mey_report_type == self.PROPOSED:
                data["form"].update(
                    {
                        "prelim_date_from": self.preliminaries_date_from,
                        "prelim_date_to": self.preliminaries_date_to,
                        "deliberation_date": self.deliberation_date,
                        "mey_report_type": self.PROPOSED,
                    }
                )
                report_id = self.env.ref("rewards.report_mey_interview_schedule")
        else:
            raise ValidationError(_("No report for this kind of awardee batch."))

        return report_id.report_action(self, data=data)

    @api.depends("awardee_batch_id")
    def _compute_award_type(self):
        """
        Update award type base on chosen awardee batch
        """
        for rec in self:
            if rec.awardee_batch_id.awardee_batch_type == rec.awardee_batch_id.CATEGORY:
                categ_id = rec.awardee_batch_id.award_category_id
                if categ_id.id == self.env.ref("rewards.award_category_mey").id:
                    rec.award_type = rec.MEY
                elif categ_id.id == self.env.ref("rewards.award_category_loyalty").id:
                    rec.award_type = rec.LOYALTY
                elif categ_id.id == self.env.ref("rewards.award_category_pbb").id:
                    rec.award_type = rec.PBB
            elif (
                rec.awardee_batch_id.awardee_batch_type
                == rec.awardee_batch_id.INDIVIDUAL
            ):
                award_id = rec.awardee_batch_id.award_id
                categ_id = award_id.award_category_id
                if award_id.id == self.env.ref("rewards.award_career").id:
                    rec.award_type = rec.CAREER
                elif categ_id.id == self.env.ref("rewards.award_category_mey").id:
                    rec.award_type = rec.MEY
                elif categ_id.id == self.env.ref("rewards.award_category_loyalty").id:
                    rec.award_type = rec.LOYALTY
                elif categ_id.id == self.env.ref("rewards.award_category_pbb").id:
                    rec.award_type = rec.PBB

    @api.onchange("awardee_batch_id", "award_type")
    def _onchange_dates(self):
        """
        Update dates from and to based on awardee_batch_id's year
        """
        if self.award_type == self.CAREER:
            year = self.awardee_batch_id.year
            self.date_from = "{}-01-01".format(year)
            self.date_to = "{}-12-31".format(year)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        """
        Check dates from and to based on awardee_batch_id's year if same year
        """
        for rec in self:
            if self.award_type == self.CAREER:
                year = int(rec.awardee_batch_id.year)
                date_from = fields.Date.from_string(rec.date_from)
                date_to = fields.Date.from_string(rec.date_to)
                if (year != date_from.year) or (year != date_to.year):
                    raise ValidationError(
                        _("Year of date must be the same as awardee batch's year.")
                    )

    @api.onchange("awardee_batch_id")
    def _onchange_mey_awardee_batch_committee(self):
        """
        Returns a domain that contains the committee members of current awardee
        batch
        """

        committee_batch_obj = self.env["rewards.mey_committee_batch"]
        res = {}

        year = self.awardee_batch_id.year
        current_batch = committee_batch_obj.get_current_committee_batch(year)

        domain = [("id", "in", current_batch.mey_committee_ids.ids)]
        res["domain"] = {"committee_member": domain}

        return res
