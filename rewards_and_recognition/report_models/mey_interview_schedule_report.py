from collections import defaultdict

from datetime import date, datetime

from odoo import api, models


class MEYInterviewScheduleReport(models.AbstractModel):
    _name = "report.rewards.mey_interview_schedule_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """

        awardee_batch_obj = self.env["rewards.awardee_batch"]
        mey_committee_obj = self.env["rewards.mey_committee"]
        interview_assessment_obj = self.env["rewards.mey_interview_assessment"]
        HELPER = self.env["utilities.helper"]

        LEVELS = [("non_sup", "NON-SUPERVISORY LEVEL"), ("sup", "SUPERVISORY LEVEL")]

        CATEGORIES = self.env["hr.employee"].NATURES_OF_WORK
        ASSESSMENT_TYPES = interview_assessment_obj.INTERVIEW_ASSESSMENT_TYPE

        rank_file_id = self.env.ref("hr_201.rank_and_file_rank")

        awardee_batch_id = data["form"]["awardee_batch_id"]
        committee_member_id = data["form"]["committee_member_id"]

        # Proposed Schedule additional details
        prelim_date = data["form"].get("prelim_date_from")
        prelim_date_end = data["form"].get("prelim_date_to")
        is_proposed_sched = data["form"].get("mey_report_type") == "proposed"
        deliberation_date = data["form"].get("deliberation_date")

        if is_proposed_sched:
            deliberation_date = HELPER.get_local_datetime(deliberation_date)

            prelim_date_format = HELPER.get_local_datetime(prelim_date)
            prelim_end_date_format = HELPER.get_local_datetime(prelim_date_end)

            if prelim_date_format.date() == prelim_end_date_format.date():
                prelim_date = "{} - {}".format(
                    prelim_date_format.strftime("%B %d, %Y : %-I:%M %p"),
                    prelim_end_date_format.strftime("%-I:%M %p"),
                )
            else:
                prelim_date = "{} - {}".format(
                    prelim_date_format.strftime("%B %d, %Y %-I:%M %p"),
                    prelim_end_date_format.strftime("%B %d, %Y %-I:%M %p"),
                )

        current_batch = awardee_batch_obj.browse(awardee_batch_id)
        committee_member = mey_committee_obj.browse(committee_member_id)

        awardees = current_batch.awardee_ids

        interview_assessments = interview_assessment_obj.search(
            [("awardee_id", "in", awardees.ids)], order="schedule_from"
        )

        date_list = []
        interview_list = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        awardee_list = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for interview in interview_assessments:
            scheduled_date = HELPER.get_local_datetime(interview.schedule_from).date()

            time_from = HELPER.get_local_datetime(interview.schedule_from)
            time_to = HELPER.get_local_datetime(interview.schedule_to)

            time_from_str = time_from.strftime("%-I:%M %p")
            time_to_str = time_to.strftime("%-I:%M %p")
            interview_time = "{} - {}".format(time_from_str, time_to_str)
            awardee = interview.awardee_id

            date_list.append(scheduled_date)

            if interview.assessment_type == interview_assessment_obj.NOMINEE:
                evaluatee_name = "{}. {}".format(
                    awardee.employee_id.first_name[0], awardee.employee_id.last_name
                )
            elif interview.assessment_type == interview_assessment_obj.CLIENT:
                evaluatee_name = interview.client_evaluatee
            else:
                evaluatee_name = "{} {}. {} {}".format(
                    interview.evaluatee_id.first_name,
                    interview.evaluatee_id.middle_name[0],
                    interview.evaluatee_id.last_name,
                    interview.evaluatee_id.extension or "",
                )

            detail = (interview.assessment_type, evaluatee_name, interview_time)

            if awardee.rank_id == rank_file_id:
                non_sup = awardee_list[scheduled_date]["non_sup"][
                    awardee.nature_of_work
                ]
                if awardee not in non_sup:
                    non_sup.append(awardee)
            else:
                sup = awardee_list[scheduled_date]["sup"][awardee.nature_of_work]
                if awardee not in sup:
                    sup.append(awardee)

            interview_list[scheduled_date][awardee][interview.assessment_type] = detail

        return {
            "interview_list": interview_list,
            "date_list": sorted(set(date_list)),
            "levels": LEVELS,
            "categories": CATEGORIES,
            "assessment_types": ASSESSMENT_TYPES,
            "awardee_list": awardee_list,
            "year": current_batch.year,
            "committee_member": committee_member,
            "prelim_date": prelim_date,
            "deliberation_date": deliberation_date,
            "is_proposed_sched": is_proposed_sched,
        }
