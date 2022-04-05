from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        res = super(StockMove, self)._prepare_move_line_vals(
            quantity, reserved_quant,
        )
        removal_priority = self.location_id.removal_priority
        picking_type_id = self.picking_type_id
        location = picking_type_id and picking_type_id.default_location or 'location_id'
        stock_location = self.env['stock.location'].browse(res[location])
        removal_priority = stock_location.removal_priority
        if picking_type_id and picking_type_id.app_integrated:
            location = picking_type_id.default_location
            res.update({
                'need_loc_before_qty': picking_type_id.need_loc_before_qty, 
                'need_location_dest_id': picking_type_id.need_location_dest_id,
                'need_location_id': picking_type_id.need_location_id,
                'need_confirm_product_id': picking_type_id.need_confirm_product_id,
                'need_confirm_lot_id': picking_type_id.need_confirm_lot_id})
        res.update({'removal_priority': removal_priority})
    
        _logger.info("StockMove VALS -------------------------\n{}".format(res))
        return res

    def _action_assign_apk_missing_qties(self):
        ### CREO STOCK MOVE LINE SCON CANTIDAD 0
        assigned_moves = self.env['stock.move']
        reserved_availability = {move: move.reserved_availability for move in self}
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available']):
            missing_reserved_uom_quantity = move.product_uom_qty - reserved_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity, move.product_id.uom_id, rounding_method='HALF-UP')
            ##SIEMPRE
            if True: ## and (move.location_id.should_bypass_reservation() or move.product_id.type == 'consu'):
                # create the move line(s) but do not impact quants. La cantidad es 0.
                if move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        self.env['stock.move.line'].create(move._prepare_move_line_vals())
                else:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                            ml.location_id == move.location_id and
                                                            ml.location_dest_id == move.location_dest_id and
                                                            ml.picking_id == move.picking_id and
                                                            not ml.lot_id and
                                                            not ml.package_id and
                                                            not ml.owner_id)
                    if to_update:

                        to_update[0].product_uom_qty += missing_reserved_uom_quantity
                        continue
                    else:
                        self.env['stock.move.line'].create(move._prepare_move_line_vals())

        
        ##partially_available_moves.write({'state': 'partially_available'})
        ##assigned_moves.write({'state': 'assigned'})
        ##self.mapped('picking_id')._check_entire_pack()
        
                
    def _action_assign(self):
        res = super()._action_assign()
        self.filtered(lambda m: m.picking_type_id and m.picking_type_id.app_integrated and m.state in ['confirmed', 'waiting', 'partially_available'])._action_assign_apk_missing_qties()
        return res