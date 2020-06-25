from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MEYCommitteeBatch(models.Model):
    """
    Rewards and Recognition Committee Batch
    """

    _name = "rewards.mey_committee_batch"
    _description = "MEY Committee Batch"
    _inherit = ["mail.thread"]

    DRAFT = "draft"
    FOR_APPROVAL = "for_approval"
    APPROVED = "approved"
    DECLINED = "declined"

    STATES = (
        (DRAFT, "Draft"),
        (FOR_APPROVAL, "For Approval"),
        (APPROVED, "Approved"),
        (DECLINED, "Declined"),
    )

    date = fields.Date(
        required=True,
        default=lambda self: fields.Date.context_today(self),
        track_visibility="onchange",
    )
    year = fields.Char(
        compute="_compute_batch_year", store=True, track_visibility="onchange"
    )
    mey_committee_ids = fields.One2many(
        comodel_name="rewards.mey_committee",
        inverse_name="mey_committee_batch_id",
        string="MEY Committee Batch Members",
        track_visibility="onchange",
    )
    state = fields.Selection(
        selection=STATES, default=DRAFT, track_visibility="onchange"
    )
    mey_interview_assessment_ids = fields.One2many(
        comodel_name="rewards.mey_interview_assessment",
        inverse_name="committee_batch_id",
        string="MEY Interview Assessments",
        track_visibility="onchange",
    )

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            name = "MEY Committee Year {}".format(rec.year)
            res.append((rec.id, name))
        return res

    @api.depends("date")
    def _compute_batch_year(self):
        """
        Compute committee batch year base on date
        """
        for rec in self:
            rec.year = fields.Date.from_string(rec.date).year

    @api.multi
    def action_draft(self):
        """
        Set record state to Draft
        """
        for rec in self:
            if rec.state in [rec.FOR_APPROVAL, rec.DECLINED]:
                rec.state = rec.DRAFT

    @api.multi
    def action_for_approval(self):
        """
        Set record state to For Approval
        """
        for rec in self:
            if rec.state == rec.DRAFT:
                rec.state = rec.FOR_APPROVAL

    @api.multi
    def action_approved(self):
        """
        Set record state to Approved
        """
        for rec in self:
            if rec.state == rec.FOR_APPROVAL:
                if (
                    self.search_count(
                        [("year", "=", rec.year), ("state", "=", rec.APPROVED)]
                    )
                    > 0
                ):
                    raise ValidationError(
                        _("Only 1 Approved MEY Committee Batch per year.")
                    )
                rec.state = rec.APPROVED

    @api.multi
    def action_declined(self):
        """
        Set record state to Declined
        """
        for rec in self:
            if rec.state in [rec.DRAFT, rec.FOR_APPROVAL]:
                rec.state = rec.DECLINED

    @api.model
    def get_current_committee_batch(self, year):
        """
        Returns approved committee batch record for the chosen year
        """
        return self.search(
            [("year", "=", year), ("state", "=", self.APPROVED)], limit=1
        )

    @api.multi
    def unlink(self):
        """
        Disable deletion if state is not draft
        """
        for rec in self:
            if rec.state != rec.DRAFT:
                raise ValidationError(
                    _("Cannot delete MEY Committee Batch that's not in Draft state.")
                )

        return super(MEYCommitteeBatch, self).unlink()


class MEYCommittee(models.Model):
    """
    Rewards and Recognition Committee Members
    """

    _name = "rewards.mey_committee"
    _description = "MEY Committee Member"
    _inherit = ["mail.thread"]
    _rec_name = "employee_id"

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        domain=([("active", "=", True), ("active_service_record", "!=", False)]),
        track_visibility="onchange",
    )
    rank_id = fields.Many2one(
        string="Rank",
        comodel_name="hr_201.rank",
        compute="_compute_employee_information",
        store=True,
        track_visibility="onchange",
    )
    assigned_position_id = fields.Many2one(
        comodel_name="hr_201.plantilla_position",
        compute="_compute_employee_information",
        store=True,
        track_visibility="onchange",
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        compute="_compute_employee_information",
        store=True,
        track_visibility="onchange",
    )
    division_id = fields.Many2one(
        comodel_name="hr.department",
        compute="_compute_employee_information",
        store=True,
        track_visibility="onchange",
    )
    mey_committee_batch_id = fields.Many2one(
        string="MEY Committee Batch",
        comodel_name="rewards.mey_committee_batch",
        required=True,
        ondelete="cascade",
        track_visibility="onchange",
    )

    @api.depends("employee_id")
    def _compute_employee_information(self):
        """
        Compute employee information based on employee_id
        """
        for rec in self:
            rec.rank_id = rec.employee_id.rank_id
            rec.assigned_position_id = rec.employee_id.assigned_position_id
            rec.department_id = rec.employee_id.department_id
            rec.division_id = rec.employee_id.division_id
