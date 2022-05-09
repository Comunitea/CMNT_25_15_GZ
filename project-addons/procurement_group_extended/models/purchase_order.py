##<button name="action_view_picking" string="Receive Products" class="oe_highlight" type="object" attrs="{'invisible': ['|', '|' , ('is_shipped', '=', True), ('state','not in', ('purchase','done')), ('picking_count', '=', 0)]}"/>
##############################################################################
#
#    Copyright (C) 2004-TODAY
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

from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.move_ids.returned_move_ids',
                 'order_line.move_ids.state',
                 'order_line.move_ids.move_dest_ids.state',
                 'order_line.move_ids.move_dest_ids.picking_id',
                 'order_line.move_ids.picking_id')
    def _compute_all_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.order_line:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                moves |= line.move_ids.mapped('move_dest_ids')
                pickings |= moves.mapped('picking_id')
            order.all_picking_ids = pickings
            order.all_picking_count = len(pickings)


    all_picking_count = fields.Integer(compute='_compute_all_picking', string='Recepciones', default=0, store=True, compute_sudo=True)
    all_picking_ids = fields.Many2many('stock.picking', compute='_compute_all_picking', string='Recepciones', copy=False, store=True, compute_sudo=True)


    @api.multi
    def action_view_picking(self):
        '''
        This function returns an action that display existing picking orders of given purchase order ids.
        When only one found, show the picking immediately.
        '''
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]

        #override the context to get rid of the default filtering on operation type
        result['context'] = {}
        pick_ids = self.mapped('all_picking_ids')
        #choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids.id
        return result