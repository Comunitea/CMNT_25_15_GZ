# © 2020 Comunitea Servicios Tecnológicos S.L. (https://comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class Holidays(models.Model):
    _inherit = "hr.holidays"

    state = fields.Selection(default="draft")

    @api.multi
    def _prepare_create_by_category(self, employee):
        values = super()._prepare_create_by_category(employee)
        values['state'] = 'confirm'
        return values
