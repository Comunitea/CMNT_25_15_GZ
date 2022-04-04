##############################################################################
#
#    Copyright (C) 2020-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Kiko Sánchez$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, exceptions, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero, float_compare

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):

    _inherit = "stock.move"

    def _action_assign(self):
        return super()._action_assign()

    
    def _action_done(self):
        res =  super()._action_done()
        self.check_bypass_stock()
        self.check_split_excess()
            
        ## self.check_split_excess_qty_move()
        return res

    def check_bypass_stock(self):
        picking_type_id = self.mapped('picking_type_id')
        if len(picking_type_id) != 1 or not picking_type_id.bypass_stock:
            return False
        
        for move in self.filtered(lambda x: x.state == 'done'):
            move_dest_id = move.move_dest_ids
            if len(move_dest_id) != 1 or not move.move_dest_ids:
                continue
            
        


    def check_split_excess(self):
        Push = self.env['stock.location.path']

        for move in self.filtered(lambda x:
            x.state == 'done' and 
            x.move_dest_ids and 
            x.product_id.type == 'product' and 
            x.product_id.picking_type_id.excess_picking_type_id):
            

            move_dest_id = move.move_dest_ids.filtered(lambda x: x.state not in ['cancel', 'draft', 'done'])
            if not move_dest_id or len(move_dest_id) > 1:
                continue
            if move_dest_ids.location_id != move.location_dest_id:
                continue
            dest_qty = sum(x.product_uom_qty - x.reserved_availability)
            



            dest_qties = sum((x.product_uom_qty - x.quantity_done) for x in move.move_dest_ids)
            
            free_qty = move.quantity_done - dest_qties
            if free_qty > 0:
                domain = [('location_from_id', '=', move.location_dest_id.id)]
                routes = move.route_ids
                rules = Push.search(domain + [('route_id', 'in', routes.ids)], order='route_sequence, sequence', limit=1)
                if rules:
                    new_move_vals = rules._prepare_move_copy_values(move, move.date_expected)
                    new_move_vals['product_uom_qty'] = free_qty
                    new_move_vals['procure_method'] = 'make_to_stock'
                    new_move_vals['rule_id'] = rules.id
                    new_move = move.copy(new_move_vals)
                    ## move.write({'move_dest_ids': [(4, new_move.id)]})
                    new_move._action_confirm()
                    new_move._action_assign()
                    
    