from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def get_warehouse_info(self):
        return [self.env.user.actual_warehouse_id.get_info()]

    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'lot_stock_id': self.lot_stock_id.get_info()
            }
        if type > 1:
            val.update({
                
            })
        if type > 2:
            val.update ({
            
            })
        _logger.info(val)
        return val
