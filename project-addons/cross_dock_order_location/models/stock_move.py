from odoo import models, fields, api, exceptions, _
from odoo.addons import decimal_precision as dp

class StockMove(models.Model):

    _inherit = "stock.move"
    
    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        res = super(StockMove, self)._prepare_move_line_vals(quantity, reserved_quant)
        if self.location_dest_id.cross_dock:
            loc_name = self.purchase_line_id.order_id.origin
            if loc_name:
                domain = [('location_id', '=', res['location_dest_id']), ('name', '=', loc_name), ('cross_dock', '=', True)]
                new_loc_dest_id = self.env['stock.location'].search(domain, limit=1)
                if new_loc_dest_id:
                    res['location_dest_id'] = new_loc_dest_id.id
        return res