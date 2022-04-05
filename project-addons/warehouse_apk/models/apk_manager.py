from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class ApkManager(models.AbstractModel):
    _name = 'apk.manager' 
    
    def return_selection_fields(self, field):
        obj = self.fields_get()['state']['selection']
        return [x for x in obj if x[0] == self[field]][0]

    @api.model
    def update_apk_options(self, values):
        user = self.env.user
        res = {}
        actual_warehouse_id = user.actual_warehouse_id or self.env['stock.warehouse'].browse(3)
        res['warehouse_id'] = actual_warehouse_id.get_info()
            

        return res

    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
        }
class StockMoveLine(models.Model):

    _inherit = ['apk.manager', 'stock.move.line']
    _name = 'stock.move.line'
