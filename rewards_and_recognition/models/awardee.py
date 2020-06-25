import statistics

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.hr_201 import common


class Awardee(models.Model):
    """
    Rewards and Recognition Awardee
    """

    _name = "rewards.awardee"
    _description = "Awardee"
    _inherit = ["mail.thread"]
    _order = "date"

    _sql_constraints = [
        (
            "unique_awardee_batch",
            "UNIQUE(awardee_batch_id, employee_id, award_id)",
            "Employee already included in the list with the same award.",
        ),
        (
            "unique_awardee",
            "UNIQUE(employee_id, award_id, year)",
            "Employee already has a record for this award this year.",
        ),
    ]

    DRAFT = "draft"
    FOR_APPROVAL = "for_approval"
    FOR_ASSESSMENT = "for_assessment"
    ASSESSED = "assessed"
    APPROVED = "approved"
    DONE = "done"
    DECLINED = "declined"

    STATES = (
        (DRAFT, "Draft"),
        (FOR_APPROVAL, "For Approval"),
        (FOR_ASSESSMENT, "For Assessment"),
        (ASSESSED, "Assessed"),
        (APPROVED, "Approved"),
        (DONE, "Done"),
        (DECLINED, "Declined"),
    )

    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"

    STATUS = (
        (QUALIFIED, "Qualified"),
        (DISQUALIFIED, "Disqualified"),
    )

    MEY = "mey"
    LOYALTY = "loyalty"
    PBB = "pbb"
    CAREER = "career"
    SERVICE = "service"

    SPECIAL_AWARDS = (
        (MEY, "MEY"),
        (LOYALTY, "Loyalty"),
        (PBB, "PBB"),
        (CAREER, "Career"),
        (SERVICE, "Service"),
    )

    state = fields.Selection(
        selection=STATES, default=DRAFT, required=True, track_visibility="onchange"
    )
    status = fields.Selection(
        selection=STATUS, default=QUALIFIED, track_visibility="onchange"
    )
    awardee_batch_id = fields.Many2one(
        comodel_name="rewards.awardee_batch",
        string="Awardee Batch",
        track_visibility="onchange",
    )
    awardee_batch_type = fields.Selection(
        related="awardee_batch_id.awardee_batch_type",
        store=True,
        track_visibility="onchange",
    )
    date = fields.Date(
        required=True,
        default=lambda self: fields.Date.context_today(self),
        track_visibility="onchange",
    )
    year = fields.Char(compute="_compute_year", track_visibility="onchange", store=True)
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        domain=([("active", "=", True), ("active_service_record", "!=", False)]),
        track_visibility="onchange",
    )
    image = fields.Binary(
        compute="_compute_employee_information", store=True, track_visibility="onchange"
    )
    assigned_position_id = fields.Many2one(
        string="Assigned Position",
        comodel_name="hr_201.plantilla_position",
        compute="_compute_employee_information",
        store=True,
        track_visibility="onchange",
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        compute="_compute_employee_information",
        string="Department",
        store=True,
        track_visibility="onchange",
    )
    division_id = fields.Many2one(
        comodel_name="hr.department",
        compute="_compute_employee_information",
        string="Division",
        store=True,
        track_visibility="onchange",
    )
    department_manager_id = fields.Many2one(
        comodel_name="hr.employee",
        compute="_compute_employee_information",
        string="Department Manager",
        store=True,
        track_visibility="onchange",
    )
    division_manager_id = fields.Many2one(
        comodel_name="hr.employee",
        compute="_compute_employee_information",
        string="Division Manager",
        store=True,
        track_visibility="onchange",
    )
    sex = fields.Selection(
        selection=lambda self: self.env["hr_201.person"].GENDER_CHOICES,
        compute="_compute_employee_information",
        store=True,
        track_visibility="onchange",
    )
    emp_status = fields.Selection(
        selection=lambda self: self.env["hr_201.service_record"].EMPLOYEE_STATUS,
        compute="_compute_employee_information",
        store=True,
        track_visibility="onchange",
    )
    award_id = fields.Many2one(
        comodel_name="rewards.award",
        string="Award",
        required=True,
        domain=[("state", "=", "approved"), ("is_active", "=", True)],
        track_visibility="onchange",
    )
    program = fields.Char(compute="_compute_reward_information", store=True)
    form_of_award = fields.Html(compute="_compute_reward_information", store=True)
    award_type = fields.Selection(
        selection=lambda self: self.env["rewards.award"].AWARD_TYPES,
        compute="_compute_reward_information",
        store=True,
        track_visibility="onchange",
    )
    is_reward_leave = fields.Boolean(compute="_compute_reward_information", store=True)
    is_reward_amount = fields.Boolean(compute="_compute_reward_information", store=True)
    reward_leave_id = fields.Many2one(
        comodel_name="hr.holidays.status",
        compute="_compute_reward_information",
        store=True,
        track_visibility="onchange",
    )
    reward_leave_count = fields.Integer(
        compute="_compute_reward_information", store=True, track_visibility="onchange"
    )
    reward_amount_type = fields.Selection(
        selection=lambda self: self.env["rewards.award"].REWARD_AMOUNT_TYPES,
        compute="_compute_reward_information",
        store=True,
        track_visibility="onchange",
    )
    reward_amount = fields.Float(
        string="Reward Amount/Percentage Basis",
        compute="_compute_reward_information",
        store=True,
        track_visibility="onchange",
    )
    amount = fields.Float(
        string="Reward",
        compute="_compute_amount",
        store=True,
        track_visibility="onchange",
    )
    remarks = fields.Html(track_visibility="onchange")
    special_award = fields.Selection(
        selection=SPECIAL_AWARDS, compute="_compute_special_award", store=True
    )
    """
    MEY Fields
    """
    nature_of_work = fields.Selection(
        selection=lambda self: self.env["hr.employee"].NATURES_OF_WORK,
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    rank_id = fields.Many2one(
        string="Rank",
        comodel_name="hr_201.rank",
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    date_of_origin = fields.Date(
        string="Date of Regularization",
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    years_of_origin = fields.Char(
        compute="_compute_awardee_information",
        store=True,
        string="Years Since Regularized",
        track_visibility="onchange",
    )
    leave_count = fields.Integer(
        string="VL/FL Count",
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    awol_count = fields.Integer(
        string="Absences Count",
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    late_count = fields.Integer(
        compute="_compute_awardee_information", store=True, track_visibility="onchange"
    )
    undertime_count = fields.Integer(
        compute="_compute_awardee_information", store=True, track_visibility="onchange"
    )
    admin_case = fields.Integer(track_visibility="onchange")
    spms_rating = fields.Selection(
        string="SPMS Rating",
        selection=lambda self: self.env["target.target_form"].RATE_NAMES,
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    schedule_from = fields.Datetime(
        default=lambda self: fields.Date.context_today(self) + " 00:00:00",
        track_visibility="onchange",
    )
    schedule_to = fields.Datetime(
        default=lambda self: fields.Date.context_today(self) + " 03:00:00",
        track_visibility="onchange",
    )
    interview_assessment_ids = fields.One2many(
        comodel_name="rewards.mey_interview_assessment",
        inverse_name="awardee_id",
        string="Interview Assessments",
        track_visibility="onchange",
    )
    interview_assessment_count = fields.Integer(
        compute="_compute_interview_assessment_count",
        string="Number of Assessments",
        store=True,
        track_visibility="onchange",
    )
    total_score = fields.Float(
        compute="_compute_total_score",
        store=True,
        group_operator="avg",
        track_visibility="onchange",
    )
    is_mey_awardee = fields.Boolean()
    """
    MEY Fields: Other Information
    """
    leave_availed_from = fields.Date(
        default=lambda self: fields.Date.context_today(self),
        track_visibility="onchange",
    )
    leave_availed_to = fields.Date(
        default=lambda self: fields.Date.context_today(self),
        track_visibility="onchange",
    )
    """
    Loyalty Fields
    """
    loyalty_date = fields.Date(
        compute="_compute_awardee_information", store=True, track_visibility="onchange"
    )
    loyalty_year = fields.Integer(
        compute="_compute_awardee_information", store=True, track_visibility="onchange"
    )
    """
    PBB Fields
    """
    salary_grade_id = fields.Many2one(
        comodel_name="hr_201.salary_grade",
        compute="_compute_awardee_information",
        string="Salary Grade",
        store=True,
        track_visibility="onchange",
    )
    salary_step_id = fields.Many2one(
        comodel_name="hr_201.salary_step",
        compute="_compute_awardee_information",
        string="Salary Step",
        store=True,
        track_visibility="onchange",
    )
    salary_amount = fields.Float(
        compute="_compute_awardee_information", store=True, track_visibility="onchange"
    )
    office_id = fields.Many2one(
        comodel_name="hr.department",
        compute="_compute_awardee_information",
        string="Delivery Unit",
        store=True,
        track_visibility="onchange",
    )
    first_period_rating = fields.Float(
        compute="_compute_awardee_information",
        store=True,
        group_operator="avg",
        track_visibility="onchange",
    )
    second_period_rating = fields.Float(
        compute="_compute_awardee_information",
        store=True,
        group_operator="avg",
        track_visibility="onchange",
    )
    average_rating = fields.Float(
        compute="_compute_awardee_information",
        store=True,
        group_operator="avg",
        track_visibility="onchange",
    )
    months_in_service = fields.Char(
        string="Months in Service (Based on Awardee Date)",
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    spms_rating_value = fields.Char(compute="_compute_awardee_information", store=True)
    """
    Career Fields
    """
    school_id = fields.Many2one(
        comodel_name="hr_201.educational_type",
        string="School",
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    course_id = fields.Many2one(
        comodel_name="hr_201.educational_type",
        string="Course",
        compute="_compute_awardee_information",
        store=True,
        track_visibility="onchange",
    )
    """
    Service Fields
    """
    date_retired = fields.Date(
        compute="_compute_awardee_information", store=True, track_visibility="onchange"
    )
    """
    Other Information
    """
    implementation_sched = fields.Char(
        string="Schedule of Implementation", track_visibility="onchange"
    )
    date_conferred = fields.Date(track_visibility="onchange")

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = "{} - {}".format(
                rec.employee_id.name, rec.awardee_batch_id.name or rec.award_id.name
            )
            res.append((rec.id, name))

        return res

    @api.onchange("awardee_batch_id")
    def _onchange_awardee_batch_id(self):
        """
        Update date of awardee record based on its awardee batch id
        Update domain of award id based on its awardee batch id category
        """
        domain = [("state", "=", "approved"), ("is_active", "=", True)]
        if self.awardee_batch_id:
            domain.append(
                ("award_category_id", "=", self.awardee_batch_id.award_category_id.id)
            )

        return {"domain": {"award_id": domain}}

    @api.depends("employee_id")
    def _compute_employee_information(self):
        """
        Compute employee information based on employee_id
        """
        for rec in self:
            rec.image = rec.employee_id.image
            rec.assigned_position_id = rec.employee_id.assigned_position_id
            rec.department_id = rec.employee_id.department_id
            rec.division_id = rec.employee_id.division_id
            rec.department_manager_id = rec.employee_id.department_id.manager_id
            rec.division_manager_id = rec.employee_id.division_id.manager_id
            rec.sex = rec.employee_id.gender
            rec.emp_status = rec.employee_id.emp_status

    @api.depends("employee_id", "special_award")
    def _compute_awardee_information(self):
        """
        Compute awardee information based on employee_id and special categ
        """

        def get_relativedelta(date_to, date_from):
            """
            Compute relativedelta between date from and to
            """
            result = None
            if date_to and date_from:
                date_from = fields.Date.from_string(date_from)
                date_to = fields.Date.from_string(date_to)
                result = relativedelta(date_to, date_from)
            return result

        for rec in self:
            if rec.special_award == rec.MEY:
                target_form_obj = self.env["target.target_form"]
                leave_obj = self.env["hr.holidays"]
                absence_obj = self.env["hr.absence"]
                attendance_obj = self.env["hr.attendance"]
                date_regular = rec.employee_id.date_regular
                years_of_origin = get_relativedelta(rec.date, date_regular)
                if years_of_origin:
                    rec.years_of_origin = "{} year(s) and {} month(s)".format(
                        years_of_origin.years, years_of_origin.months
                    )
                    rec.date_of_origin = date_regular
                rec.nature_of_work = rec.employee_id.nature_of_work
                rec.rank_id = rec.employee_id.rank_id
                rec.leave_count = leave_obj.get_total_vl_fl(rec.employee_id, rec.year)
                rec.awol_count = absence_obj.get_awol_count(rec.employee_id, rec.year)
                rec.late_count = attendance_obj.get_late_count(
                    rec.employee_id, rec.year
                )
                rec.undertime_count = attendance_obj.get_ut_count(
                    rec.employee_id, rec.year
                )
                rec.spms_rating = target_form_obj.get_target_rates(
                    rec.employee_id, rec.year
                ).get("adjectival_rating")
                rec.spms_rating_value = dict(target_form_obj.RATE_NAMES).get(
                    rec.spms_rating
                )
            elif rec.special_award == rec.LOYALTY:
                rec.loyalty_date = rec.employee_id.loyalty_date
                rec.loyalty_year = rec.employee_id.loyalty_year
            elif rec.special_award == rec.PBB:
                service_rec = rec.employee_id.active_service_record
                target_form_obj = self.env["target.target_form"]
                target_rates = target_form_obj.get_target_rates(
                    rec.employee_id, rec.year
                )
                rec.salary_grade_id = service_rec.salary_grade_id
                rec.salary_step_id = service_rec.salary_step_id
                rec.salary_amount = service_rec.salary_amount
                rec.spms_rating = target_rates.get("adjectival_rating")
                rec.spms_rating_value = dict(target_form_obj.RATE_NAMES).get(
                    rec.spms_rating
                )
                rec.first_period_rating = target_rates.get("first_period_rating")
                rec.second_period_rating = target_rates.get("second_period_rating")
                rec.average_rating = target_rates.get("average_rating")
                rec.office_id = (
                    rec.employee_id.department_id.parent_id
                    if rec.employee_id.department_id.parent_id
                    else rec.employee_id.department_id
                )
                rec.rank_id = rec.employee_id.rank_id
                months_in_service = get_relativedelta(
                    rec.date, rec.employee_id.date_regular
                )
                if months_in_service:
                    if months_in_service.years >= 1:
                        rec.months_in_service = "12"
                    else:
                        rec.months_in_service = "{} month(s) and {} day(s)".format(
                            months_in_service.months, months_in_service.days
                        )
            elif rec.special_award == rec.CAREER:
                education_id = rec.employee_id.education_ids.filtered(
                    lambda edu, rec=rec: int(edu.year_to) == int(rec.year)
                )
                education_id = (
                    education_id if len(education_id) <= 1 else education_id[0]
                )
                rec.school_id = education_id.school
                rec.course_id = education_id.course_id
            elif rec.special_award == rec.SERVICE:
                rec.date_retired = rec.employee_id.active_service_record.end_date

    @api.depends("interview_assessment_ids")
    def _compute_interview_assessment_count(self):
        """
        Compute number of interview assessments for the awardee
        """
        for rec in self:
            rec.interview_assessment_count = len(rec.interview_assessment_ids)

    @api.depends("interview_assessment_ids.score", "interview_assessment_ids.state")
    def _compute_total_score(self):
        """
        Compute total score (average) of an awardee's interview assessments
        """
        for rec in self:
            interview_assessment_ids = rec.interview_assessment_ids.filtered(
                lambda ass: ass.state == ass.DONE
            )
            score = interview_assessment_ids.mapped("score")
            if score:
                rec.total_score = common.round_up(statistics.mean(score))

    @api.depends("date")
    def _compute_year(self):
        """
        Compute year base on date field
        """
        for rec in self:
            rec.year = fields.Date.from_string(rec.date).year

    @api.depends("award_id")
    def _compute_reward_information(self):
        """
        Update rewards boolean to hide specific fields
        Update rewards fields based on award_id
        """
        for rec in self:
            rec.program = rec.award_id.program
            rec.form_of_award = rec.award_id.form_of_award
            rec.award_type = rec.award_id.award_type
            rec.reward_leave_id = rec.award_id.reward_leave_id
            rec.reward_leave_count = rec.award_id.reward_leave_count
            rec.reward_amount_type = rec.award_id.reward_amount_type
            rec.reward_amount = rec.award_id.reward_amount

            if rec.award_type == rec.award_id.MONETARY:
                rec.is_reward_leave = rec.reward_leave_id.id is not False
                rec.is_reward_amount = rec.reward_amount_type is not False
            elif rec.award_type == rec.award_id.NONMONETARY:
                rec.is_reward_leave = False
                rec.is_reward_amount = False

    @api.depends("award_id")
    def _compute_special_award(self):
        """
        Update special award to hide specific fields
        """
        for rec in self:
            categ_id = rec.award_id.award_category_id
            if categ_id.id == self.env.ref("rewards.award_category_mey").id:
                rec.special_award = rec.MEY
            elif categ_id.id == self.env.ref("rewards.award_category_loyalty").id:
                rec.special_award = rec.LOYALTY
            elif categ_id.id == self.env.ref("rewards.award_category_pbb").id:
                rec.special_award = rec.PBB
            elif rec.award_id.id == self.env.ref("rewards.award_career").id:
                rec.special_award = rec.CAREER
            elif rec.award_id.id == self.env.ref("rewards.award_service").id:
                rec.special_award = rec.SERVICE

    @api.depends("employee_id", "reward_amount_type", "reward_amount")
    def _compute_amount(self):
        """
        Compute amount based on reward_amount_type and reward_amount
        """
        for rec in self:
            if rec.award_type == rec.award_id.MONETARY:
                if rec.reward_amount_type == rec.award_id.FIXED_AMOUNT:
                    rec.amount = rec.reward_amount
                elif rec.reward_amount_type == rec.award_id.SALARY_PERCENTAGE:
                    rec.amount = rec.employee_id.active_service_record.salary_amount * (
                        rec.reward_amount / 100
                    )
            elif rec.award_type == rec.award_id.NONMONETARY:
                rec.amount = 0

    @api.constrains("schedule_from", "schedule_to", "year")
    def _check_schedule(self):
        """
        Checks schedule if it's within the year
        """
        for rec in self:
            if (
                fields.Date.from_string(rec.schedule_from).year
                or fields.Date.from_string(rec.schedule_to).year
            ) != int(rec.year):
                raise ValidationError(
                    _("Schedule must be within the year {}").format(rec.year)
                )

    @api.constrains("award_id")
    def _check_award_id(self):
        """
        Checks if award_id category matches awardee batch category
        """
        for rec in self:
            if (
                rec.awardee_batch_id
                and rec.award_id.award_category_id
                != rec.awardee_batch_id.award_category_id
            ):
                raise ValidationError(
                    _(
                        "Award must be in the same category selected in awardee batch record"
                    )
                )

    @api.constrains("employee_id", "award_id")
    def _check_employee_id(self):
        """
        Check if employee_id is still eligible for the chosen award_id
        Check if employee_id is not a MEY Committee for this year
        """
        for rec in self:
            committee_batch_obj = self.env["rewards.mey_committee_batch"]
            commitee_batch_id = committee_batch_obj.get_current_committee_batch(
                rec.year
            )
            com_employee_ids = commitee_batch_id.mey_committee_ids.mapped("employee_id")
            if rec.employee_id in com_employee_ids and rec.special_award == rec.MEY:
                raise ValidationError(
                    _(
                        "Employee is a MEY Committee and is not eligible for the MEY Award."
                    )
                )

            mey_categ_id = self.env.ref("rewards.award_category_mey")
            if rec.award_id.award_category_id == mey_categ_id and self.search(
                [
                    ("id", "!=", self.id),
                    ("employee_id", "=", rec.employee_id.id),
                    ("is_mey_awardee", "=", True),
                ]
            ):
                raise ValidationError(
                    _(
                        "Employee is already a MEY Awardee and is no longer eligible for the MEY Award."
                    )
                )

    @api.multi
    def action_open_interview_assessment_ids(self):
        """
        Triggered function when 'Interview Assessments' button is clicked.
        Returns an action window with specific context, domain, and view_id
        """
        action = self.env.ref("rewards.act_window_mey_interview_assessment")
        action_data = action.read().pop()
        action_data.update(
            {
                "context": {
                    "default_awardee_id": self.id,
                    "default_schedule_from": self.schedule_from,
                    "default_schedule_to": self.schedule_to,
                },
                "domain": [("awardee_id", "=", self.id)],
            }
        )

        return action_data

    @api.multi
    def action_generate_interview_assessments(self):
        """
        Triggered function when 'Generate Interview Assessments' button is clicked.
        """
        assessment_obj = self.env["rewards.mey_interview_assessment"]
        assessment_types = assessment_obj.INTERVIEW_ASSESSMENT_TYPE
        rank_file_id = self.env.ref("hr_201.rank_and_file_rank").id
        for rec in self:
            existing_assessments = rec.interview_assessment_ids
            for assessment_type in assessment_types:

                if assessment_type[0] not in existing_assessments.mapped(
                    "assessment_type"
                ) and not (
                    rec.rank_id.id == rank_file_id
                    and assessment_type[0] == "subordinate"
                ):
                    assessment_obj.create(
                        {
                            "assessment_type": assessment_type[0],
                            "awardee_id": rec.id,
                            "schedule_from": rec.schedule_from,
                            "schedule_to": rec.schedule_to,
                        }
                    )

    @api.multi
    def action_print_scoresheets(self):
        """
        Prints the MEY Scoresheets of the Candidate
        """

        rank_file_id = self.env.ref("hr_201.rank_and_file_rank").id

        for rec in self:
            is_rank_file = rec.rank_id.id == rank_file_id

            data = {
                "form": {
                    "employee_name": rec.employee_id.name,
                    "awardee_id": rec.id,
                    "dept_code": rec.department_id.code,
                    "assigned_position_name": rec.assigned_position_id.name,
                    "interview_assessment_ids": rec.interview_assessment_ids.ids,
                    "year": rec.year,
                    "is_rank_file": is_rank_file,
                },
            }
        return self.env.ref("rewards.report_mey_scoresheet").report_action(
            self, data=data
        )

    @api.multi
    def action_draft(self):
        """
        Set record state to Draft
        """
        for rec in self:
            if rec.state in [rec.FOR_APPROVAL, rec.DECLINED]:
                rec.state = rec.DRAFT
                rec.status = rec.QUALIFIED

    @api.multi
    def action_for_approval(self):
        """
        Set record state to For Approval
        """
        for rec in self:
            if rec.state == rec.DRAFT:
                rec.state = rec.FOR_APPROVAL

    @api.multi
    def action_for_assessment(self):
        """
        Set record state to For Assessment
        """
        for rec in self:
            if rec.state == rec.FOR_APPROVAL:
                rec.state = rec.FOR_ASSESSMENT

    @api.multi
    def action_assessed(self):
        """
        Set record state to Assessed
        """
        for rec in self:
            if rec.state == rec.FOR_ASSESSMENT:
                if rec.status is rec.DISQUALIFIED:
                    raise ValidationError(
                        _("Awardee is disqualified and cannot be assessed.")
                    )
                for ass_id in rec.interview_assessment_ids.filtered(
                    lambda ass_id: ass_id.state != ass_id.DECLINED
                ):
                    ass_id.state = ass_id.DONE
                rec.state = rec.ASSESSED

    @api.multi
    def action_approved(self):
        """
        Set record state to Approved
        """
        for rec in self:
            if rec.state == rec.FOR_APPROVAL:
                if rec.status is rec.DISQUALIFIED:
                    raise ValidationError(
                        _("Awardee is disqualified and cannot be approved.")
                    )
                rec.state = rec.APPROVED

    @api.multi
    def action_done(self):
        """
        Set record state to Done
        """
        for rec in self:
            rec.state = rec.DONE
            award_mey_awardee_ids = [
                self.env.ref("rewards.award_mey_awardee_supv_field"),
                self.env.ref("rewards.award_mey_awardee_supv_office"),
                self.env.ref("rewards.award_mey_awardee_nonsupv_field"),
                self.env.ref("rewards.award_mey_awardee_nonsupv_office"),
            ]
            if rec.award_id in award_mey_awardee_ids:
                rec.is_mey_awardee = True

    @api.multi
    def action_declined(self):
        """
        Set record state to Declined
        """
        for rec in self:
            if rec.state in [rec.DRAFT, rec.FOR_APPROVAL]:
                rec.state = rec.DECLINED
                rec.status = rec.DISQUALIFIED

    @api.multi
    def unlink(self):
        """
        Disable deletion if state is not draft
        """
        for rec in self:
            if rec.state != rec.DRAFT:
                raise ValidationError(
                    _("Cannot delete awardee that's not in draft state.")
                )

        return super(Awardee, self).unlink()

    def get_gm(self, awardee_ids):
        """
        Get General Manager from awardee_ids
        """
        gm_rank_id = self.env.ref("hr_201.general_manager_rank")
        gm_id = awardee_ids.filtered(
            lambda awardee_id: awardee_id.rank_id == gm_rank_id
        )
        gm_id = gm_id if len(gm_id) <= 1 else gm_id[0]

        return gm_id
