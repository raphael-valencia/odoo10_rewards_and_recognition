from odoo import api, models
from odoo.addons.hr_201 import common


class PBBDeliveryUnitsReport(models.AbstractModel):
    _name = "report.rewards.pbb_delivery_units_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """
        form = data["form"]
        emp_obj = self.env["hr.employee"]
        department_obj = self.env["hr.department"]
        awardee_batch_obj = self.env["rewards.awardee_batch"]
        awardee_obj = self.env["rewards.awardee"]

        awardee_batch_id = awardee_batch_obj.browse(form["awardee_batch_id"])
        gm_id = awardee_obj.get_gm(awardee_batch_id.awardee_ids)
        no_gm_awardee_ids = awardee_batch_id.awardee_ids.filtered(
            lambda awardee_id: awardee_id != gm_id
        ).sorted(
            key=lambda awardee_id: (awardee_id.award_id.id, awardee_id.employee_id.name)
        )

        rank_delivery_unit_list = []

        for awardee_id in no_gm_awardee_ids:
            # Gets existing dict of rank from rank_delivery_unit_list
            rank = common.get_dict_item(
                rank_delivery_unit_list, "award_id", awardee_id.award_id
            )
            # If dict of rank doesn't exist, create a new dict
            if not rank:
                rank_delivery_unit_list.append(
                    {
                        "award_id": awardee_id.award_id,
                        "office_list": [
                            {
                                "office_id": awardee_id.office_id,
                                "department_list": [
                                    {
                                        "department_id": awardee_id.department_id,
                                        "awardee_list": [
                                            {"index": 1, "awardee_id": awardee_id}
                                        ],
                                    }
                                ],
                                "count": 1,
                                "amount": awardee_id.amount,
                                "row_span": 4,
                            }
                        ],
                        "subtotal_count": 1,
                        "subtotal_amount": awardee_id.amount,
                        "row_span": 5,
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
                            "office_id": awardee_id.office_id,
                            "department_list": [
                                {
                                    "department_id": awardee_id.department_id,
                                    "awardee_list": [
                                        {"index": 1, "awardee_id": awardee_id}
                                    ],
                                }
                            ],
                            "count": 1,
                            "amount": awardee_id.amount,
                            "row_span": 4,
                        }
                    )
                    rank["row_span"] += 4
                else:
                    department_list = office.get("department_list")
                    # Gets existing dict of department from office
                    department = common.get_dict_item(
                        department_list, "department_id", awardee_id.department_id
                    )
                    # If dict of department doesn't exist, create a new dict
                    if not department:
                        department_list.append(
                            {
                                "department_id": awardee_id.department_id,
                                "awardee_list": [
                                    {"index": 1, "awardee_id": awardee_id}
                                ],
                            }
                        )
                        rank["row_span"] += 2
                        office["row_span"] += 2
                    else:
                        department.get("awardee_list").append(
                            {
                                "index": len(department.get("awardee_list")) + 1,
                                "awardee_id": awardee_id,
                            }
                        )
                        rank["row_span"] += 1
                        office["row_span"] += 1
                    office["count"] += 1
                    office["amount"] += awardee_id.amount
                rank["subtotal_count"] += 1
                rank["subtotal_amount"] += awardee_id.amount

        return {
            "awardee_batch_id": awardee_batch_id,
            "rank_delivery_unit_list": rank_delivery_unit_list,
            "hr_dept_manager_id": department_obj.get_hr_department_manager(),
            "gm_id": gm_id,
            "employee_no_pbb_ids": emp_obj.browse(form["employee_no_pbb_ids"]),
            "employee_no_saln_ids": emp_obj.browse(form["employee_no_saln_ids"]),
            "employee_no_ca_ids": emp_obj.browse(form["employee_no_ca_ids"]),
            "employee_no_spms_ids": emp_obj.browse(form["employee_no_spms_ids"]),
            "employee_excluded_ids": emp_obj.browse(form["employee_excluded_ids"]),
        }
