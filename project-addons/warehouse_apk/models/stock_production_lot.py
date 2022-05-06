from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
            'ref': self.ref,
            }
        if type > 1:
            val.update({
                
            })
        if type > 2:
            val.update ({

            })
        return val
    
    def create_if_not_exits(self, names, product_id):
        lot_ids = self.env['stock.production.lot']
        for name in names:
            domain = [('product_id', '=', product_id), '|', ('name', '=', name), ('ref', '=', name)]
            lot_id = self.env['stock.production.lot'].search(domain, limit=1)
            if not lot_id:
                lot_vals = {'name': name, 'product_id': product_id}
                lot_id = self.create(lot_vals) 
            lot_ids |= lot_id
            
        return lot_ids
