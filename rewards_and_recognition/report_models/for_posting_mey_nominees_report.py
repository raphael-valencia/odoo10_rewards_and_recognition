from collections import defaultdict

from odoo import api, models


class ForPostingMEYNomineesReport(models.AbstractModel):
    _name = "report.rewards.for_posting_mey_nominees_report_template"

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

        mey_nominees = current_batch.awardee_ids.sorted(
            key=lambda r: r.employee_id.name
        )

        result = defaultdict(lambda: defaultdict(list))

        for nominee in mey_nominees:
            if nominee.rank_id == rank_file_id:
                result["non_sup"][nominee.nature_of_work].append(nominee)
            else:
                result["sup"][nominee.nature_of_work].append(nominee)

        return {
            "levels": LEVELS,
            "categories": CATEGORIES,
            "result": result,
            "committee_member": committee_member,
            "year": current_batch.year,
        }
