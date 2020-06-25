from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class Employee(models.Model):
    """
    This is an inherited model used for rewards and recognition specific
    field declarations.
    """

    _inherit = ["hr.employee"]

    loyalty_date = fields.Date(track_visibility="onchange")
    loyalty_year = fields.Integer(
        compute="_compute_loyalty_year", store=True, track_visibility="onchange"
    )
    awardee_ids = fields.One2many(
        comodel_name="rewards.awardee", inverse_name="employee_id", string="Awards"
    )

    @api.model
    def _cron_set_emp_loyalty_date(self):
        """
        Scheduled task: Set loyalty date of each employee each year.
        """

        hr_absence_object = self.env["hr.absence"]
        hr_holidays_object = self.env["hr.holidays"]
        study_leave_id = self.env.ref("hr_credits.hr_holidays_status_06")
        employees = self.search([])

        for emp in employees:
            emp_awol_absences = hr_absence_object.search_count(
                [
                    ("employee_id", "=", emp.id),
                    ("on_date", ">=", emp.date_hire),
                    ("absent_type", "=", "awol"),
                ]
            )

            total_days = emp_awol_absences

            emp_lwops = hr_holidays_object.search(
                [
                    ("type", "=", "remove"),
                    ("employee_id", "=", emp.id),
                    ("state", "=", "validate"),
                    ("date_from", ">=", emp.date_hire),
                    ("dwop", ">", 0),
                    ("holiday_status_id", "!=", study_leave_id.id),
                ]
            )

            total_days += sum(emp_lwops.mapped("dwop"))
            total_days += abs(emp.lost_service_days)

            date_hire = fields.Date.from_string(emp.date_hire)
            loyalty_date = date_hire + timedelta(days=total_days)

            emp.loyalty_date = loyalty_date

    @api.depends("loyalty_date")
    def _compute_loyalty_year(self):
        """
        Compute loyalty year base on today and employee's loyalty date
        """
        for rec in self:
            rec.loyalty_year = relativedelta(
                fields.date.today(), fields.Date.from_string(rec.loyalty_date)
            ).years
