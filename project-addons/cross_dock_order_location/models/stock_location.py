from odoo import models, fields, api, exceptions, _
from odoo.addons import decimal_precision as dp



class StockLocation(models.Model):

    _inherit = "stock.location"

    cross_dock = fields.Boolean("Cross Dock", default=False)


    ## Debería llamarse a esta acción para liberar y archivar stock_location
    def _check_free_cross_dock_location(self, group_id):
        domain = [('location_id.cross_dock', '=', False), ('quant_ids', '=', False), ('cross_dock', '=', True)]
        cross_dock_loc = self.env['stock.location'].search(loc_name)
        for loc in cross_dock_loc:
            move_domain = [('location_dest_id', '=', loc.id)]
            move_ids = self.env['stock.move.line'].search(move_domain).mapped('move_id')
            if all(x.state in [('cancel', 'done')] for x in move_ids):
                loc.active = False
        return False