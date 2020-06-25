from odoo import api, fields, models


class AwardeeActionWizard(models.TransientModel):
    """
    Awardee Action Wizard that appears upon clicking 'Update Awardee'
    from Awardee Tree View Action Dropdown
    """

    _name = "rewards.awardee_action_wizard"
    _description = "Awardee Action Wizard"

    award_id = fields.Many2one(
        string="Award",
        comodel_name="rewards.award",
        domain=[("state", "=", "approved"), ("is_active", "=", True)],
    )
    implementation_sched = fields.Char(string="Schedule of Implementation")
    date_conferred = fields.Date()

    @api.multi
    def action_update_awardee(self):
        """
        Updates selected awardee's info if awardee's state is in draft or for approval
        """
        for rec in self:
            awardee_ids = self.env["rewards.awardee"].browse(
                self.env.context.get("active_ids")
            )
            for awardee_id in awardee_ids.filtered(
                lambda awardee_id: awardee_id.state
                not in [awardee_id.DONE, awardee_id.DECLINED]
            ):
                if rec.award_id:
                    awardee_id.award_id = rec.award_id
                if rec.implementation_sched:
                    awardee_id.implementation_sched = rec.implementation_sched
                if rec.date_conferred:
                    awardee_id.date_conferred = rec.date_conferred
