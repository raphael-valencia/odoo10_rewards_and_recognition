from odoo import api, models


class MEYScoresheetReport(models.AbstractModel):
    _name = "report.rewards.mey_scoresheet_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """

        committee_batch_obj = self.env["rewards.mey_committee_batch"]
        interview_assessment_obj = self.env["rewards.mey_interview_assessment"]
        awardee_obj = self.env["rewards.awardee"]

        employee_name = data["form"]["employee_name"]
        dept_code = data["form"]["dept_code"]
        assigned_position_name = data["form"]["assigned_position_name"]
        year = data["form"]["year"]
        is_rank_file = data["form"]["is_rank_file"]
        interview_assessments = interview_assessment_obj.browse(
            data["form"]["interview_assessment_ids"]
        )
        awardee = awardee_obj.browse(data["form"]["awardee_id"])

        committee_batch = committee_batch_obj.get_current_committee_batch(awardee.year)

        return {
            "employee_name": employee_name,
            "awardee_img": awardee.image,
            "dept_code": dept_code,
            "assigned_position": assigned_position_name,
            "year": year,
            "position": assigned_position_name,
            "is_rank_file": is_rank_file,
            "interviews": interview_assessments,
            "committee_members": committee_batch.mey_committee_ids,
        }
