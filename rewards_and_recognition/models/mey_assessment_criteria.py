from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MEYAssessmentCriteria(models.Model):
    _name = "rewards.mey_assessment_criteria"
    _description = "MEY Assessment Criteria"
    _inherit = ["mail.thread"]

    name = fields.Char(
        string="Criteria Name", track_visibility="onchange", required=True
    )
    percentage = fields.Float(
        string="Percentage (%)", required=True, track_visibility="onchange"
    )
    is_active = fields.Boolean(
        default=True, track_visibility="onchange", string="Active"
    )
    assessment_result_ids = fields.One2many(
        comodel_name="rewards.mey_assessment_result",
        inverse_name="criteria_id",
        string="Assessment Results",
        track_visibility="onchange",
    )

    @api.constrains("percentage", "is_active")
    def _active_criteria_limit(self):
        """
        Checks if the total percentage of active criteria is not more than 100%
        """
        active_records = self.env["rewards.mey_assessment_criteria"].search(
            [("is_active", "=", True)]
        )

        if sum(active_records.mapped("percentage")) > 100:
            raise ValidationError(
                _("Total percentage of active criteria must not exceed 100%.")
            )
