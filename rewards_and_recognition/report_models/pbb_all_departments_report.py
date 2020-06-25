from odoo import api, models
from odoo.addons.hr_201 import common


class PBBAllDepartmentsReport(models.AbstractModel):
    _name = "report.rewards.pbb_all_departments_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """
        form = data["form"]
        awardee_batch_obj = self.env["rewards.awardee_batch"]
        emp_obj = self.env["hr.employee"]
        awardee_obj = self.env["rewards.awardee"]

        awardee_batch_id = awardee_batch_obj.browse(form["awardee_batch_id"])
        gm_id = awardee_obj.get_gm(awardee_batch_id.awardee_ids)
        no_gm_awardee_ids = awardee_batch_id.awardee_ids.filtered(
            lambda awardee_id: awardee_id != gm_id
        ).sorted(
            key=lambda awardee_id: (awardee_id.award_id.id, awardee_id.employee_id.name)
        )

        department_list = []

        for awardee_id in no_gm_awardee_ids:
            # Gets existing dict of department from department_list
            department = common.get_dict_item(
                department_list, "department_id", awardee_id.department_id
            )
            # If dict of department_id doesn't exist, create a new dict
            if not department:
                department_list.append(
                    {
                        "department_id": awardee_id.department_id,
                        "awardee_list": [{"index": 1, "awardee_id": awardee_id}],
                        "subtotal": awardee_id.amount,
                    }
                )
            else:
                awardee_list = department["awardee_list"]
                awardee_list.append(
                    {"index": len(awardee_list) + 1, "awardee_id": awardee_id}
                )
                department["subtotal"] += awardee_id.amount

        return {
            "awardee_batch_id": awardee_batch_id,
            "department_list": department_list,
            "total_count": len(no_gm_awardee_ids),
            "total_amount": sum(no_gm_awardee_ids.mapped("amount")),
            "prepared_by_id": emp_obj.browse(form["prepared_by_id"]),
            "checked_by_id": emp_obj.browse(form["checked_by_id"]),
            "noted_by_id": emp_obj.browse(form["noted_by_id"]),
        }
