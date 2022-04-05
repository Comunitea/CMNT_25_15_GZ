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

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_stock_move_ids(self):
        for sale in self:
            pickings = self.procurement_group_id.picking_ids
            stock_move_ids = pickings.mapped('move_lines')
            sale.stock_move_ids = stock_move_ids
            sale.stock_move_ids_count = len(stock_move_ids)

    stock_move_ids = fields.One2many('stock.move', compute="_get_stock_move_ids")
    stock_move_ids_count = fields.Integer(compute="_get_stock_move_ids")

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.procurement_group_id.picking_ids)

    @api.multi
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        
        action = super().action_view_delivery()
        pickings = self.procurement_group_id.picking_ids
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action
    
    def action_picking_move_tree(self):
        ctx = self.env.context.copy()
        ctx.update({
                    'search_default_by_product': True,
                    'search_default_groupby_picking_type': True,
                    })
        action = self.env.ref('stock.stock_move_action').read()[0]
        action['views'] = [
            (self.env.ref('custom_warehouse.view_picking_move_tree_cw').id, 'tree'),
        ]
        action['context'] = ctx
        action['domain'] = [('id', 'in', self.stock_move_ids.sorted(key=lambda l: l.id).ids)]

        return action

class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def name_get(self):
        result = []
        for so_line in self:
            name = '%s - %s' % (so_line.order_id.name, so_line.name.split('\n')[0] or so_line.product_id.name)
            if so_line.order_partner_id.ref:
                name = '%s (%s)' % (name, so_line.order_partner_id.ref)
            name = '%s Qty: %s %s' % (name, so_line.product_uom_qty, so_line.product_uom.name)
            result.append((so_line.id, name))
        return result