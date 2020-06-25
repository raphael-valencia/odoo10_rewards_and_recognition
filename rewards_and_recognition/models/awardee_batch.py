from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AwardeeBatch(models.Model):
    """
    Rewards and Recognition Awardee Batch
    """

    _name = "rewards.awardee_batch"
    _description = "Award Batch"
    _inherit = ["mail.thread"]
    _order = "date"

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

    CATEGORY = "category"
    INDIVIDUAL = "individual"

    AWARDEE_BATCH_TYPE = (
        (CATEGORY, "By Category Award"),
        (INDIVIDUAL, "By Indivual Award"),
    )

    name = fields.Char(compute="_compute_name", store=True, track_visibility="onchange")
    state = fields.Selection(
        selection=STATES, default=DRAFT, track_visibility="onchange"
    )
    date = fields.Date(
        required=True,
        default=lambda self: fields.Date.context_today(self),
        track_visibility="onchange",
    )
    year = fields.Char(compute="_compute_year", store=True, track_visibility="onchange")
    award_category_id = fields.Many2one(
        comodel_name="rewards.award_category",
        string="Award Category",
        track_visibility="onchange",
    )
    award_id = fields.Many2one(
        comodel_name="rewards.award",
        string="Award",
        domain=[("state", "=", "approved"), ("is_active", "=", True)],
        track_visibility="onchange",
    )
    remarks = fields.Html(track_visibility="onchange")
    awardee_batch_type = fields.Selection(
        selection=AWARDEE_BATCH_TYPE,
        default=CATEGORY,
        required=True,
        track_visibility="onchange",
    )
    awardee_ids = fields.One2many(
        comodel_name="rewards.awardee",
        inverse_name="awardee_batch_id",
        string="Awardee",
        track_visibility="onchange",
    )
    total_count = fields.Integer(
        compute="_compute_awardee_count", store=True, track_visibility="onchange"
    )
    total_male_count = fields.Integer(
        compute="_compute_awardee_count", store=True, track_visibility="onchange"
    )
    total_female_count = fields.Integer(
        compute="_compute_awardee_count", store=True, track_visibility="onchange"
    )
    total_amount = fields.Float(
        compute="_compute_awardee_reward_amount",
        store=True,
        track_visibility="onchange",
    )
    is_mey_categ = fields.Boolean(
        compute="_compute_is_mey_categ", store=True, track_visibility="onchange"
    )
    """
    MEY Fields: Criteria
    """
    mey_permanent_employee_year = fields.Integer(
        string="Permanent Employee No. of Years",
        compute="_compute_mey_criteria_information",
        store=True,
        track_visibility="onchange",
    )
    mey_late_undertime_count = fields.Integer(
        string="No. of Tardiness/Undertime",
        compute="_compute_mey_criteria_information",
        store=True,
        track_visibility="onchange",
    )
    mey_awol_count = fields.Integer(
        string="No. of Unauthorized Absences",
        compute="_compute_mey_criteria_information",
        store=True,
        track_visibility="onchange",
    )
    mey_leave_count = fields.Integer(
        string="No. of Vacation/Forced Leaves",
        compute="_compute_mey_criteria_information",
        store=True,
        track_visibility="onchange",
    )
    mey_admin_case = fields.Integer(
        string="No. of Admin Cases",
        compute="_compute_mey_criteria_information",
        store=True,
        track_visibility="onchange",
    )
    mey_spms_rating = fields.Selection(
        string="SPMS Rating",
        selection=lambda self: self.env["target.target_form"].RATE_NAMES,
        compute="_compute_mey_criteria_information",
        store=True,
        track_visibility="onchange",
    )
    mey_other_criteria = fields.Html(
        compute="_compute_mey_criteria_information",
        store=True,
        track_visibility="onchange",
    )

    @api.onchange("award_id")
    def _onchange_award_id(self):
        self.award_category_id = self.award_id.award_category_id.id

    @api.depends("awardee_ids.amount")
    def _compute_awardee_reward_amount(self):
        """
        Compute total reward amount of awardees
        """
        for rec in self:
            rec.total_amount = sum(rec.awardee_ids.mapped("amount"))

    @api.depends("awardee_ids")
    def _compute_awardee_count(self):
        """
        Compute total number of awardees
        """
        for rec in self:
            rec.total_count = len(rec.awardee_ids)
            rec.total_male_count = len(
                rec.awardee_ids.filtered(lambda awrd: awrd.employee_id.gender == "male")
            )
            rec.total_female_count = len(
                rec.awardee_ids.filtered(
                    lambda awrd: awrd.employee_id.gender == "female"
                )
            )

    @api.depends("awardee_batch_type", "award_category_id", "award_id")
    def _compute_is_mey_categ(self):
        """
        Compute mey categ boolean based on award category
        """
        for rec in self:
            mey_categ_id = self.env.ref("rewards.award_category_mey")
            if rec.awardee_batch_type == rec.CATEGORY:
                rec.is_mey_categ = rec.award_category_id == mey_categ_id
            if rec.awardee_batch_type == rec.INDIVIDUAL:
                rec.is_mey_categ = rec.award_id.award_category_id == mey_categ_id

    @api.depends("is_mey_categ")
    def _compute_mey_criteria_information(self):
        """
        Compute mey criteria information based on mey categ boolean
        """
        for rec in self:
            if rec.is_mey_categ:
                mey_categ_id = self.env.ref("rewards.award_category_mey")
                rec.mey_permanent_employee_year = (
                    mey_categ_id.mey_permanent_employee_year
                )
                rec.mey_late_undertime_count = mey_categ_id.mey_late_undertime_count
                rec.mey_awol_count = mey_categ_id.mey_awol_count
                rec.mey_leave_count = mey_categ_id.mey_leave_count
                rec.mey_admin_case = mey_categ_id.mey_admin_case
                rec.mey_spms_rating = mey_categ_id.mey_spms_rating
                rec.mey_other_criteria = mey_categ_id.mey_other_criteria

    @api.depends("date", "awardee_batch_type", "award_category_id", "award_id")
    def _compute_name(self):
        """
        Compute name base on year and award category/award
        """
        for rec in self:
            if rec.awardee_batch_type == rec.CATEGORY:
                rec.display_name = rec.award_category_id.name
            elif rec.awardee_batch_type == rec.INDIVIDUAL:
                rec.display_name = rec.award_id.name

            rec.name = "{} {}".format(rec.year, rec.display_name)

    @api.depends("date")
    def _compute_year(self):
        """
        Compute year base on date field
        """
        for rec in self:
            rec.year = fields.Date.from_string(rec.date).year

    @api.multi
    def action_open_awardee_ids(self):
        """
        Triggered function when 'Awardees' button is clicked.
        Returns an action window with specific context, domain, and view_id
        """
        categ_id = self.award_category_id or self.award_id.award_category_id

        if categ_id.id == self.env.ref("rewards.award_category_mey").id:
            tree_id = self.env.ref("rewards.view_mey_awardee_tree")
            context = {
                "search_default_groupby_dept": 1,
                "default_award_id": self.env.ref("rewards.award_mey_fields").id,
            }
        elif categ_id.id == self.env.ref("rewards.award_category_pbb").id:
            tree_id = self.env.ref("rewards.view_pbb_awardee_tree")
            context = {
                "search_default_groupby_delivery_dept": 1,
                "default_award_id": self.env.ref("rewards.award_pbb_good").id,
            }
        else:
            tree_id = self.env.ref("rewards.view_awardee_tree")
            context = {
                "search_default_groupby_award": 1,
                "search_default_groupby_dept": 1,
                "default_award_id": self.award_id.id,
            }

        context.update(
            {"default_awardee_batch_id": self.id, "default_date": self.date,}
        )

        form_id = self.env.ref("rewards.view_awardee_form")
        action = self.env.ref("rewards.act_window_awardee")
        action_data = action.read().pop()
        action_data.update(
            {
                "context": context,
                "domain": [("awardee_batch_id", "=", self.id)],
                "views": [(tree_id.id, "tree"), (form_id.id, "form")],
            }
        )

        return action_data

    @api.multi
    def action_generate_awardees(self):
        """
        Triggered function when 'Generate Awardees' button is clicked.
        """

        def get_or_create_awardee(awardee_batch_id, award_id):
            """
            Create awardee for awardee batch if
            award belongs to special categories (MEY, Loyalty, PBB).
            Get awardee with the same award and that has no awardee batch.
            """
            leave_obj = self.env["hr.holidays"]
            absence_obj = self.env["hr.absence"]
            attendance_obj = self.env["hr.attendance"]
            awardee_obj = self.env["rewards.awardee"]
            service_rec_obj = self.env["hr_201.service_record"]
            employee_obj = self.env["hr.employee"]
            target_form_obj = self.env["target.target_form"]
            mey_committee_batch_obj = self.env["rewards.mey_committee_batch"]
            loyalty_categ_id = self.env.ref("rewards.award_category_loyalty")
            mey_categ_id = self.env.ref("rewards.award_category_mey")
            pbb_categ_id = self.env.ref("rewards.award_category_pbb")
            is_special_categ = award_id.award_category_id in [
                loyalty_categ_id,
                pbb_categ_id,
                mey_categ_id,
            ]
            is_service_award = award_id == self.env.ref("rewards.award_service")

            def create_awardee(employee_id, award_id):
                awardee_obj.create(
                    {
                        "date": awardee_batch_id.date,
                        "awardee_batch_id": awardee_batch_id.id,
                        "award_id": award_id.id,
                        "employee_id": employee_id.id,
                    }
                )

            # GET AWARDEE

            # Include existing awardees (without a batch) in this batch
            awardee_obj.search(
                [
                    ("awardee_batch_id", "=", False),
                    ("award_id", "=", award_id.id),
                    ("year", "=", awardee_batch_id.year),
                ]
            ).write({"awardee_batch_id": awardee_batch_id.id})

            # CREATE AWARDEE

            # Create awardees (Only applicable for special categories or service_award
            # Since these categories and award have conditions)
            if is_special_categ or is_service_award:
                if award_id.award_category_id in [pbb_categ_id, mey_categ_id]:
                    employee_ids = target_form_obj.search(
                        [
                            ("year", "=", awardee_batch_id.year),
                            ("state", "=", target_form_obj.RATED),
                        ]
                    ).mapped("employee_id")
                    if award_id.award_category_id == mey_categ_id:
                        # Exclude mey committees and mey winners
                        mey_committee_ids = mey_committee_batch_obj.search(
                            [
                                ("year", "=", awardee_batch_id.year),
                                ("state", "=", mey_committee_batch_obj.APPROVED),
                            ]
                        ).mey_committee_ids.mapped("employee_id")
                        mey_awardee_ids = awardee_obj.search(
                            [("is_mey_awardee", "=", True)]
                        ).mapped("employee_id")
                        employee_ids = [
                            emp_id
                            for emp_id in employee_ids
                            if emp_id not in mey_committee_ids + mey_awardee_ids
                        ]
                else:
                    employee_ids = employee_obj.search(
                        [("active", "=", True), ("active_service_record", "!=", False)]
                    )

                # Awardees included in this batch
                existing_awardees = awardee_batch_id.awardee_ids.mapped("employee_id")
                for employee_id in employee_ids:
                    if employee_id not in existing_awardees:
                        # Loyalty Award Category
                        if (award_id.award_category_id == loyalty_categ_id) and (
                            employee_id.loyalty_year == award_id.loyalty_year
                        ):
                            create_awardee(employee_id, award_id)
                        # Service Award
                        elif is_service_award and service_rec_obj.check_retired(
                            employee_id, awardee_batch_id.year
                        ):
                            create_awardee(employee_id, award_id)

                        # MEY Award
                        elif award_id.award_category_id == mey_categ_id:
                            date_regular = employee_id.date_regular
                            if date_regular:
                                # Compute years of origin based on employee's date regularized
                                # and awaree record date
                                date_of_origin = fields.Date.from_string(date_regular)
                                date = fields.Date.from_string(awardee_batch_id.date)
                                years_of_origin = relativedelta(
                                    date, date_of_origin
                                ).years
                            else:
                                years_of_origin = 0
                            leave_count = leave_obj.get_total_vl_fl(
                                employee_id, awardee_batch_id.year
                            )
                            awol_count = absence_obj.get_awol_count(
                                employee_id, awardee_batch_id.year
                            )
                            late_count = attendance_obj.get_late_count(
                                employee_id, awardee_batch_id.year
                            )
                            undertime_count = attendance_obj.get_ut_count(
                                employee_id, awardee_batch_id.year
                            )
                            spms_rating = target_form_obj.get_target_rates(
                                employee_id, awardee_batch_id.year
                            ).get("adjectival_rating")
                            mey_perm_emp_year = (
                                awardee_batch_id.mey_permanent_employee_year
                            )
                            mey_late_ut_count = (
                                awardee_batch_id.mey_late_undertime_count
                            )
                            mey_awol_count = awardee_batch_id.mey_awol_count
                            mey_leave_count = awardee_batch_id.mey_leave_count
                            mey_spms_rating = awardee_batch_id.mey_spms_rating
                            if (
                                (years_of_origin >= mey_perm_emp_year)
                                and (
                                    sum([late_count, undertime_count])
                                    <= mey_late_ut_count
                                )
                                and (awol_count <= mey_awol_count)
                                and (leave_count <= mey_leave_count)
                                and (int(spms_rating) >= int(mey_spms_rating))
                            ):
                                create_awardee(employee_id, award_id)
                        # PBB Award
                        elif award_id.award_category_id == pbb_categ_id:
                            create_awardee(employee_id, award_id)

        for rec in self:
            award_obj = self.env["rewards.award"]
            if rec.awardee_batch_type == rec.CATEGORY:
                mey_categ_id = self.env.ref("rewards.award_category_mey")
                pbb_categ_id = self.env.ref("rewards.award_category_pbb")
                award_id = {
                    mey_categ_id: self.env.ref("rewards.award_mey_fields"),
                    pbb_categ_id: self.env.ref("rewards.award_pbb_good"),
                }
                if rec.award_category_id in [mey_categ_id, pbb_categ_id]:
                    get_or_create_awardee(rec, award_id.get(rec.award_category_id))
                else:
                    award_ids = award_obj.search(
                        [
                            ("award_category_id", "=", rec.award_category_id.id),
                            ("is_active", "=", True),
                            ("state", "=", award_obj.APPROVED),
                        ]
                    )
                    for award_id in award_ids:
                        get_or_create_awardee(rec, award_id)
            elif rec.awardee_batch_type == rec.INDIVIDUAL:
                get_or_create_awardee(rec, rec.award_id)

    @api.multi
    def action_draft(self):
        """
        Set record state to Draft
        """
        for rec in self:
            if rec.state == rec.DECLINED:
                rec.state = rec.DRAFT

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
                for awardee_id in rec.awardee_ids.filtered(
                    lambda awardee_id: awardee_id.state != awardee_id.DECLINED
                ):
                    awardee_id.action_done()
                rec.state = rec.DONE

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
                    _("Cannot delete award batch that's not in draft state.")
                )

        return super(AwardeeBatch, self).unlink()
