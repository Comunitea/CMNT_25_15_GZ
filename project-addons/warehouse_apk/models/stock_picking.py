from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)



class StockPicking(models.Model):
    _inherit = 'stock.picking'
    

    @api.model
    def action_validate_apk(self, values):
        
        return True

    
    @api.model
    def get_picking_info(self, values):
        ## ['id', 'name', 'sale_id', 'scheduled_date', 'origin', 'state', 'partner_id', 'move_line_ids']
        picking_id = self.browse(values.get('id', False))
        info_type = values.get('info_type', 0)       
        return self.get_info(info_type)
    
    def get_info(self, info_type = 0):
        if not self:
            return
        vals = {
            'id': self.id,
            'name': self.name,
            'sale_id': self.sale_id.get_info(),
            'partner_id': self.partner_id.get_info(),
            'purchase_id':self.purchase_id.get_info(),
            'origin': self.origin,
            'scheduled_date': self.scheduled_date,
            ##'user_id':  {'id': p_id.user_id.id, 'name': p_id.user_id.name},
            'state': p_id.state,
            'picking_type_id': p_id.picking_type_id.get_info()
        }
        if info_type > 0:
            vals.update({
                'destination_code_id': self.destination_code_id.get_info(),
                'move_type': self.move_type,
                'priority': self.priority,
                'all_asigned': self.all_asigned,
                'forced': self.forced,
                'product_uomo_qty': self.product_uom_qty,
                'reserved_availability': self.reserved_availability,
                'quantity_done': self.quantity_done
            })
        _logger.info("Devuelvo {}".format(vals) )
        return vals