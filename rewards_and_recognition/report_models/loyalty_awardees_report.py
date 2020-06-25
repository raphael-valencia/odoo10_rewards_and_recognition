from collections import defaultdict

from odoo import api, models, _
from odoo.exceptions import ValidationError


class LoyaltyAwardeesReport(models.AbstractModel):
    _name = "report.rewards.loyalty_awardees_report_template"

    @api.model
    def get_report_values(self, docids, data=None):
        """
        Fetch the report values to be passed on the report template
        """

        awardee_batch_id = data["form"]["awardee_batch_id"]

        params = [awardee_batch_id]

        query = """
                    SELECT
                        ROW_NUMBER () OVER (PARTITION BY ard.loyalty_year ORDER BY ade.loyalty_date, emp.name ) as row_num,
                        UPPER(CONCAT(emp.last_name, ', ', emp.first_name,' ',emp.extension, LEFT(emp.middle_name, 1))) emp_name,
                        ade.loyalty_date as loyalty_date,
                        ard.loyalty_year as loyalty_year
                    FROM
                        rewards_awardee as ade,
                        rewards_award as ard,
                        hr_employee as emp
                    WHERE
                        ade.employee_id = emp.id AND
                        ade.award_id = ard.id AND
                        ade.awardee_batch_id = %s
                    ORDER BY ard.loyalty_year
                """

        self.env.cr.execute(query, params)
        query_result = self.env.cr.fetchall()

        if not query_result:
            raise ValidationError(
                _("No data to display on generation. (List of Loyalty Awardees)")
            )

        result = defaultdict(list)
        sorted_years = []
        for row in query_result:
            result[row[3]].append(row[:3])
            sorted_years.append(row[3])

        sorted_years = sorted(list(set(sorted_years)))

        return {"sorted_years": sorted_years, "result": result}
