from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MEYInterviewAssessment(models.Model):
    """
    Rewards and Recognition Interview Assessment Records
    """

    _name = "rewards.mey_interview_assessment"
    _description = "MEY Interview Assessment"
    _inherit = ["mail.thread"]

    NOMINEE = "nominee"
    SUPERVISOR = "supervisor"
    PEER = "peer"
    CLIENT = "client"
    SUBORDINATE = "subordinate"

    INTERVIEW_ASSESSMENT_TYPE = (
        (SUPERVISOR, "Supervisor"),
        (PEER, "Peer"),
        (CLIENT, "Client"),
        (SUBORDINATE, "Subordinate"),
        (NOMINEE, "Nominee"),
    )

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DECLINED = "declined"

    STATES = (
        (DRAFT, "Draft"),
        (IN_PROGRESS, "In Progress"),
        (DONE, "Done"),
        (DECLINED, "Declined"),
    )

    assessment_type = fields.Selection(
        selection=INTERVIEW_ASSESSMENT_TYPE,
        default=NOMINEE,
        required=True,
        track_visibility="onchange",
    )
    evaluatee_id = fields.Many2one(
        comodel_name="hr.employee",
        track_visibility="onchange",
        string="Evaluatee (Employee)",
    )
    client_evaluatee = fields.Char(
        string="Evaluatee (Client)", track_visibility="onchange"
    )
    schedule_from = fields.Datetime(
        default=lambda self: fields.Date.context_today(self) + " 00:00:00",
        track_visibility="onchange",
    )
    schedule_to = fields.Datetime(
        default=lambda self: fields.Date.context_today(self) + " 03:00:00",
        track_visibility="onchange",
    )
    state = fields.Selection(
        selection=STATES, default=DRAFT, track_visibility="onchange"
    )
    assessment_result_ids = fields.One2many(
        comodel_name="rewards.mey_assessment_result",
        inverse_name="interview_assessment_id",
        string="Assessment Results",
        track_visibility="onchange",
    )
    score = fields.Float(
        string="Assessment Score",
        compute="_compute_assessment_score",
        store=True,
        group_operator="avg",
        track_visibility="onchange",
    )
    awardee_id = fields.Many2one(
        comodel_name="rewards.awardee",
        string="Awardee",
        required=True,
        domain=[("special_award", "=", "mey")],
        ondelete="cascade",
        track_visibility="onchange",
    )
    rank_id = fields.Many2one(
        string="Rank",
        related="awardee_id.rank_id",
        store=True,
        track_visibility="onchange",
    )
    year = fields.Char(
        related="awardee_id.year", store=True, track_visibility="onchange"
    )
    committee_batch_id = fields.Many2one(
        comodel_name="rewards.mey_committee_batch",
        string="Committee Batch",
        compute="_compute_committee_batch",
        store=True,
        track_visibility="onchange",
    )
    remarks = fields.Html(track_visibility="onchange",)

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

    @api.constrains("year")
    def _check_committee_batch(self):
        """
        Checks if committee batch is set
        """
        for rec in self:
            if not rec.committee_batch_id:
                raise ValidationError(
                    _("No approved committee batch set based on year {}").format(
                        rec.year
                    )
                )

    @api.depends("year")
    def _compute_committee_batch(self):
        """
        Computes committee batch for the year
        """
        for rec in self:
            committee_batch_obj = self.env["rewards.mey_committee_batch"]
            rec.committee_batch_id = committee_batch_obj.get_current_committee_batch(
                rec.year
            )

    @api.depends("assessment_result_ids")
    def _compute_assessment_score(self):
        """
        Computes sum of assessment result's score
        """
        for rec in self:
            rec.score = sum(rec.assessment_result_ids.mapped("score"))

    @api.model
    def create(self, vals):
        """
        Creates assessment results based on number of active criteria
        """
        rec = super(MEYInterviewAssessment, self).create(vals)
        active_criteria = self.env["rewards.mey_assessment_criteria"].search(
            [("is_active", "=", True)]
        )

        for criteria in active_criteria:
            assessment_results = self.env["rewards.mey_assessment_result"]
            assessment_results.create(
                {"interview_assessment_id": rec.id, "criteria_id": criteria.id}
            )

        return rec

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            interview_assessment_type = dict(rec.INTERVIEW_ASSESSMENT_TYPE)
            name = "MEY Interview Assessment ({}) - {} {}".format(
                interview_assessment_type.get(rec.assessment_type),
                rec.awardee_id.employee_id.name,
                self.env["utilities.helper"]
                .get_local_datetime(rec.schedule_from)
                .strftime("%b. %d, %Y %I:%M %p"),
            )
            res.append((rec.id, name))
        return res

    @api.multi
    def action_in_progress(self):
        """
        Set record state to In Progress
        """
        for rec in self:
            if rec.state == rec.DRAFT:
                rec.state = rec.IN_PROGRESS

    @api.multi
    def action_done(self):
        """
        Set record state to Done
        """
        for rec in self:
            if rec.state == rec.IN_PROGRESS:
                rec.state = rec.DONE

    @api.multi
    def action_draft(self):
        """
        Set record state to Draft
        """
        for rec in self:
            if rec.state == rec.DECLINED:
                rec.state = rec.DRAFT

    @api.multi
    def action_declined(self):
        """
        Set record state to Declined
        """
        for rec in self:
            if rec.state == rec.DRAFT:
                rec.state = rec.DECLINED

    @api.multi
    def unlink(self):
        """
        Disable deletion if state is not draft
        """
        for rec in self:
            if rec.state != rec.DRAFT:
                raise ValidationError(
                    _(
                        "Cannot delete MEY Interview Assessment that's not in Draft state."
                    )
                )

        return super(MEYInterviewAssessment, self).unlink()


class MEYAssessmentResult(models.Model):
    """
    Rewards and Recognition Assessment Results
    """

    _name = "rewards.mey_assessment_result"
    _description = "MEY Assessment Result"
    _inherit = ["mail.thread"]

    interview_assessment_id = fields.Many2one(
        comodel_name="rewards.mey_interview_assessment",
        string="Interview Assessment",
        track_visibility="onchange",
        required=True,
        ondelete="cascade",
    )
    criteria_id = fields.Many2one(
        comodel_name="rewards.mey_assessment_criteria", track_visibility="onchange"
    )
    criteria_percentage = fields.Float(
        string="Base Percentage (%)",
        compute="_compute_criteria_percentage",
        track_visibility="onchange",
        store=True,
    )
    score = fields.Float(track_visibility="onchange", default=0)
    state = fields.Selection(
        related="interview_assessment_id.state",
        track_visibility="onchange",
        store=True,
        readonly=True,
    )

    @api.depends("criteria_id")
    def _compute_criteria_percentage(self):
        """
        Compute criteria percentage based on criteria_id's percentage
        """
        for rec in self:
            rec.criteria_percentage = rec.criteria_id.percentage

    @api.constrains("score")
    def _limit_assessment_score(self):
        """
        Checks if score given is not more than the criteria base percentage
        """
        for rec in self:
            if rec.score > rec.criteria_percentage:
                raise ValidationError(
                    _("Criteria Score cannot be higher than Base Percentage.")
                )
