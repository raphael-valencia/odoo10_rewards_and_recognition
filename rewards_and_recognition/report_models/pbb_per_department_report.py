from odoo import api, models
from odoo.addons.hr_201 import common


class PBBPerDepartmentReport(models.AbstractModel):
    _name = "report.rewards.pbb_per_department_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """
        form = data["form"]
        awardee_batch_obj = self.env["rewards.awardee_batch"]
        awardee_obj = self.env["rewards.awardee"]

        awardee_batch_id = awardee_batch_obj.browse(form["awardee_batch_id"])
        no_gm_awardee_ids = awardee_batch_id.awardee_ids.filtered(
            lambda awardee_id: awardee_id
            != awardee_obj.get_gm(awardee_batch_id.awardee_ids)
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
                        "average_rating": awardee_id.average_rating,
                        "total": awardee_id.amount,
                        "manager_id": awardee_id.department_id.manager_id,
                    }
                )
            else:
                awardee_list = department["awardee_list"]
                awardee_list_len = len(awardee_list) + 1
                awardee_list.append(
                    {"index": awardee_list_len, "awardee_id": awardee_id}
                )
                department["average_rating"] = common.round_up(
                    (department["average_rating"] + awardee_id.average_rating)
                    / awardee_list_len
                )
                department["total"] += awardee_id.amount

        return {
            "awardee_batch_id": awardee_batch_id,
            "department_list": department_list,
        }
