from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)



class StockLocation(models.Model):
    _inherit = 'stock.location'

    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,

            'barcode': self.barcode,
            'usage': self.usage,
            'removal_priority': self.removal_priority
            }
        if type > 1:
            val.update({
                
            })
        if type > 2:
            val.update ({

            })
        return val
    
    @api.model
    def get_warehouse_locations(self, values):
        _logger.info(self._context)
        lot_stock_id = self.env.user.actual_warehouse_id.lot_stock_id
        d1 = [('id', '!=', self.env.user.actual_warehouse_id.id)]
        lot_stock_ids = self.env['stock.warehouse'].search(d1).mapped('lot_stock_id')
        not_location_ids_domain = [('location_id', 'child_of', lot_stock_ids.ids)]
        location_ids = self.search(not_location_ids_domain)
        location_ids = self.search([('id', 'not in', location_ids.ids), ('barcode', '!=', False)])
        res=[]
        for loc in location_ids:
            _logger.info(loc.name)
            res.append(loc.get_info())
        return res
