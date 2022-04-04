from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)



class ResUser(models.Model):
    _inherit = 'res.users'

    actual_warehouse_id = fields.Many2one('stock.warehouse', string="Selected Warehouse")

    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
            }
        if type > 1:
            val.update({
            })
        if type > 2:
            val.update ({
            })
        return val