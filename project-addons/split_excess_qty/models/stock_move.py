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


    excess_picking_type_id = fields.Many2one(related="picking_id.excess_picking_type_id")

    def _action_assign(self):
        return super()._action_assign()

    
    def _action_done(self):
        
        res =  super()._action_done()
        self.check_split_excess()
        return res
    
    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        vals['excess_picking_type_id'] = self.picking_type_id.excess_picking_type_id and self.picking_type_id.excess_picking_type_id.id or False
        return vals
    
    def check_split_excess(self):
        Push = self.env['procurement.rule']
        self = self.with_prefetch()
        for move in self.filtered(lambda x: x.state == 'done' and x.picking_type_id.excess_picking_type_id and x.product_id.type == 'product'):
            ## and x.product_id.picking_type_id.excess_picking_type_id):
            move_dest_id = move.move_dest_ids.filtered(lambda x: x.state  == 'assigned')
            if len(move_dest_id) != 1:
                continue
            if move_dest_id.location_id != move.location_dest_id:
                continue
            free_qty = move.quantity_done - move_dest_id.reserved_availability
            if free_qty > 0:
                ## El destino viene del tipo de  albaran para excess_qty
                excess_picking_type_id = move.picking_type_id.excess_picking_type_id
                location_dest_id = excess_picking_type_id.default_location_dest_id
                location_id = move.location_dest_id
                domain = [('location_id', '=', location_dest_id.id), ('location_src_id', '=', location_id.id)]

                routes = move.route_ids
                rules = Push.search(domain + [('route_id', 'in', routes.ids)], order='route_sequence, sequence', limit=1)
                if not rules:
                    rules = Push.search(domain, order='route_sequence, sequence', limit=1)
                if not rules:
                    raise ValidationError("No se encontrado una ragla de {} a {}".format(location_id.display_name, location_dest_id.dsiplay_name))
                if rules:
                    defaults = move.with_context(force_split_uom_id=move.product_id.uom_id.id)._prepare_move_split_vals(free_qty)
                    if defaults.get('move_dest_ids'):
                        defaults.pop('move_dest_ids')
                    defaults['move_orig_ids'] = [(4, move.id)]
                    defaults['procure_method'] = 'make_to_stock'
                    defaults['rule_id'] = rules.id
                    defaults['location_dest_id'] = location_dest_id.id
                    defaults['location_id'] = move.location_dest_id.id
                    defaults['picking_type_id'] = excess_picking_type_id.id
                    defaults['picking_id'] = False
                    
                    new_move = move.with_context(rounding_method='HALF-UP').copy(defaults)
                    new_move._action_confirm()
                    new_move._action_assign()
                    
    