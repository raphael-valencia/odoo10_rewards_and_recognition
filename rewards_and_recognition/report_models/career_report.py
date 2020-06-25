from odoo import fields, api, models
from odoo.addons.hr_201 import common


class CareerReport(models.AbstractModel):
    _name = "report.rewards.career_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """
        form = data["form"]
        date_format = "%B %Y"
        awardee_batch_obj = self.env["rewards.awardee_batch"]
        emp_obj = self.env["hr.employee"]

        awardee_ids = awardee_batch_obj.browse(
            form["awardee_batch_id"]
        ).awardee_ids.filtered(
            lambda awardee_id: (awardee_id.date <= form["date_to"])
            and (awardee_id.date >= form["date_from"])
        )

        return {
            "awardee_ids": common.get_list_count(awardee_ids),
            "date_from": fields.Date.from_string(form["date_from"]).strftime(
                date_format
            ),
            "date_to": fields.Date.from_string(form["date_to"]).strftime(date_format),
            "prepared_by_id": emp_obj.browse(form["prepared_by_id"]),
            "checked_by_id": emp_obj.browse(form["checked_by_id"]),
            "noted_by_id": emp_obj.browse(form["noted_by_id"]),
        }
