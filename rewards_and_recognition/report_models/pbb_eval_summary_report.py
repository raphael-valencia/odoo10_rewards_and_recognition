from odoo import api, models
from odoo.addons.hr_201 import common


class PBBEvalSummaryReport(models.AbstractModel):
    _name = "report.rewards.pbb_eval_summary_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """
        form = data["form"]
        department_obj = self.env["hr.department"]
        awardee_batch_obj = self.env["rewards.awardee_batch"]
        awardee_obj = self.env["rewards.awardee"]

        awardee_ids = awardee_batch_obj.browse(form["awardee_batch_id"]).awardee_ids
        # Get General Manager
        gm_rank_id = self.env.ref("hr_201.general_manager_rank")
        gm_id = (
            awardee_ids.filtered(lambda awardee_id: awardee_id.rank_id == gm_rank_id)
            or awardee_obj
        )
        gm_id = gm_id if len(gm_id) <= 1 else gm_id[0]

        eval_summary_list = []

        for awardee_id in awardee_ids.filtered(
            lambda awardee_id: awardee_id != gm_id
        ).sorted(key=lambda awardee_id: awardee_id.award_id.id):
            # Gets existing dict of rank from eval_summary_list
            rank = common.get_dict_item(
                eval_summary_list, "award_id", awardee_id.award_id
            )
            # If dict of rank doesn't exist, create a new dict
            if not rank:
                eval_summary_list.append(
                    {
                        "award_id": awardee_id.award_id,
                        "office_list": [
                            {
                                "index": 1,
                                "office_id": awardee_id.office_id,
                                "count": 1,
                                "amount": awardee_id.amount,
                            }
                        ],
                        "subtotal_count": 1,
                        "subtotal_amount": awardee_id.amount,
                    }
                )
            else:
                office_list = rank.get("office_list")
                # Gets existing dict of office from rank
                office = common.get_dict_item(
                    office_list, "office_id", awardee_id.office_id
                )
                # If dict of office doesn't exist, create a new dict
                if not office:
                    office_list.append(
                        {
                            "index": len(office_list) + 1,
                            "office_id": awardee_id.office_id,
                            "count": 1,
                            "amount": awardee_id.amount,
                        }
                    )
                else:
                    office["count"] += 1
                    office["amount"] += awardee_id.amount
                rank["subtotal_count"] += 1
                rank["subtotal_amount"] += awardee_id.amount

        return {
            "eval_summary_list": eval_summary_list,
            "total_count": len(awardee_ids),
            "total_amount": sum(awardee_ids.mapped("amount")),
            "hr_dept_manager_id": department_obj.get_hr_department_manager(),
            "gm_id": gm_id,
        }
