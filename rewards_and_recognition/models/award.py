from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AwardCategory(models.Model):
    """
    Rewards and Recognition Awards Category Configuration
    """

    _name = "rewards.award_category"
    _description = "Award Category"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, track_visibility="onchange")
    award_ids = fields.One2many(
        comodel_name="rewards.award",
        inverse_name="award_category_id",
        string="Awards",
        track_visibility="onchange",
    )
    awardee_batch_ids = fields.One2many(
        comodel_name="rewards.awardee_batch",
        inverse_name="award_category_id",
        string="Awardee Batch",
        track_visibility="onchange",
    )
    is_default = fields.Boolean()
    is_mey_category = fields.Boolean()
    """
    MEY Criteria
    """
    mey_permanent_employee_year = fields.Integer(
        string="Permanent Employee No. of Years", track_visibility="onchange"
    )
    mey_late_undertime_count = fields.Integer(
        string="No. of Tardiness/Undertime", track_visibility="onchange"
    )
    mey_awol_count = fields.Integer(
        string="No. of Unauthorized Absences", track_visibility="onchange"
    )
    mey_leave_count = fields.Integer(
        string="No. of Vacation/Forced Leaves", track_visibility="onchange"
    )
    mey_admin_case = fields.Integer(
        string="No. of Admin Cases", track_visibility="onchange"
    )
    mey_spms_rating = fields.Selection(
        string="SPMS Rating",
        selection=lambda self: self.env["target.target_form"].RATE_NAMES,
        track_visibility="onchange",
    )
    mey_other_criteria = fields.Html(track_visibility="onchange")

    @api.multi
    def unlink(self):
        """
        Disable deletion of default award categories
        """
        for rec in self:
            if rec.is_default:
                raise ValidationError(_("Cannot delete a default award category."))

        return super(AwardCategory, self).unlink()


class Award(models.Model):
    """
    Rewards and Recognition Awards Configuration
    """

    _name = "rewards.award"
    _description = "Award"
    _inherit = ["mail.thread"]
    _order = "award_category_id"

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

    MONETARY = "monetary"
    NONMONETARY = "nonmonetary"
    OTHER = "other"

    AWARD_TYPES = (
        (MONETARY, "Monetary"),
        (NONMONETARY, "Non-Monetary"),
        (OTHER, "Other Incentives"),
    )

    FIXED_AMOUNT = "fixed_amount"
    SALARY_PERCENTAGE = "salary_percentage"

    REWARD_AMOUNT_TYPES = (
        (FIXED_AMOUNT, "Fixed Amount"),
        (SALARY_PERCENTAGE, "Salary Percentage"),
    )

    award_type = fields.Selection(
        selection=AWARD_TYPES,
        default=MONETARY,
        required=True,
        track_visibility="onchange",
    )
    award_type_value = fields.Char(compute="_compute_award_type_value", store=True,)
    name = fields.Char(required=True, track_visibility="onchange")
    state = fields.Selection(
        selection=STATES, default=DRAFT, track_visibility="onchange"
    )
    form_of_award = fields.Html(track_visibility="onchange")
    loyalty_year = fields.Integer(track_visibility="onchange")
    is_loyalty = fields.Boolean(
        compute="_compute_is_loyalty", store=True, track_visibility="onchange"
    )
    award_category_id = fields.Many2one(
        comodel_name="rewards.award_category",
        string="Award Category",
        track_visibility="onchange",
    )
    reward_amount_type = fields.Selection(
        selection=REWARD_AMOUNT_TYPES, track_visibility="onchange"
    )
    reward_amount = fields.Float(
        string="Reward Amount/Percentage", track_visibility="onchange"
    )
    reward_leave_id = fields.Many2one(
        comodel_name="hr.holidays.status",
        string="Reward Leave Type",
        track_visibility="onchange",
    )
    reward_leave_count = fields.Integer(track_visibility="onchange")
    is_active = fields.Boolean(string="Active", track_visibility="onchange")
    awardee_batch_ids = fields.One2many(
        comodel_name="rewards.awardee_batch",
        inverse_name="award_id",
        string="Awardee Batch",
        track_visibility="onchange",
    )
    awardee_ids = fields.One2many(
        comodel_name="rewards.awardee",
        inverse_name="award_id",
        string="Awardee",
        track_visibility="onchange",
    )
    is_default = fields.Boolean()
    program = fields.Char(
        compute="_compute_program", store=True, track_visibility="onchange"
    )

    @api.depends("name", "award_category_id")
    def _compute_program(self):
        """
        Compute RnR program name base category or name
        """
        for rec in self:
            rec.program = rec.award_category_id.name or rec.name

    @api.depends("award_type")
    def _compute_award_type_value(self):
        """
        Compute equivalent selection value of award type
        """
        for rec in self:
            rec.award_type_value = dict(rec.AWARD_TYPES).get(rec.award_type)

    @api.depends("award_category_id")
    def _compute_is_loyalty(self):
        """
        Method to hide loyalty_year field in award form
        """
        for rec in self:
            if (
                rec.award_category_id.id
                == self.env.ref("rewards.award_category_loyalty").id
            ):
                rec.is_loyalty = True
            else:
                rec.is_loyalty = False

    @api.multi
    def action_draft(self):
        """
        Set record state to Draft
        """
        for rec in self:
            if rec.state in [rec.FOR_APPROVAL, rec.APPROVED, rec.DECLINED]:
                rec.state = rec.DRAFT
                rec.is_active = False

    @api.multi
    def action_for_approval(self):
        """
        Set record state to For Approval
        """
        for rec in self:
            if rec.state == rec.DRAFT:
                rec.state = rec.FOR_APPROVAL
                rec.is_active = False

    @api.multi
    def action_approved(self):
        """
        Set record state to Approved
        """
        for rec in self:
            if rec.state == rec.FOR_APPROVAL:
                rec.state = rec.APPROVED
                rec.is_active = True

    @api.multi
    def action_declined(self):
        """
        Set record state to Declined
        """
        for rec in self:
            if rec.state in [rec.DRAFT, rec.FOR_APPROVAL]:
                rec.state = rec.DECLINED
                rec.is_active = False

    @api.multi
    def unlink(self):
        """
        Disable deletion if state is not draft
        """
        for rec in self:
            if rec.state != rec.DRAFT:
                raise ValidationError(
                    _("Cannot delete award that's not in Draft state.")
                )
            if rec.is_default:
                raise ValidationError(_("Cannot delete a default award."))

        return super(Award, self).unlink()
