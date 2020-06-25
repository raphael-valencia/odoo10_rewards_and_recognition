from collections import defaultdict

from odoo import api, models


class QualifiedMEYNomineesReport(models.AbstractModel):
    _name = "report.rewards.qualified_mey_nominees_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """

        LEVELS = [("non_sup", "NON-SUPERVISORY LEVEL"), ("sup", "SUPERVISORY LEVEL")]

        CATEGORIES = self.env["hr.employee"].NATURES_OF_WORK

        awardee_batch_obj = self.env["rewards.awardee_batch"]
        mey_committee_obj = self.env["rewards.mey_committee"]

        rank_file_id = self.env.ref("hr_201.rank_and_file_rank")

        awardee_batch_id = data["form"]["awardee_batch_id"]
        committee_member_id = data["form"]["committee_member_id"]

        current_batch = awardee_batch_obj.browse(awardee_batch_id)
        committee_member = mey_committee_obj.browse(committee_member_id)

        mey_nominees = current_batch.awardee_ids.filtered(
            lambda awardee_id: awardee_id.status == awardee_id.QUALIFIED
        )
        mey_nominees = mey_nominees.sorted(key=lambda r: r.employee_id.name)

        result = defaultdict(lambda: defaultdict(list))

        for nominee in mey_nominees:
            if nominee.rank_id == rank_file_id:
                result["non_sup"][nominee.nature_of_work].append(nominee)
            else:
                result["sup"][nominee.nature_of_work].append(nominee)

        total_male = current_batch.total_male_count
        total_female = current_batch.total_female_count
        total_count = current_batch.total_count

        return {
            "levels": LEVELS,
            "categories": CATEGORIES,
            "result": result,
            "committee_member": committee_member,
            "male_count": total_male,
            "female_count": total_female,
            "total_count": total_count,
            "criteria_no_of_years": current_batch.mey_permanent_employee_year,
            "criteria_ut_late_count": current_batch.mey_late_undertime_count,
            "criteria_vl_count": current_batch.mey_leave_count,
            "year": current_batch.year,
        }
