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


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    merge_moves = fields.Boolean("Merge moves", help="If true, merge diferent move lines in same move", default=True)

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    @api.multi
    def compute_sale_ids_count(self):
        for pick in self:
            pick.sale_ids_count = len(pick.sale_ids)
    # sale_id = fields.Many2one(related='', comodel_name='sale.order', string="Sale order", compute=_compute_sale_for_picking)
    sale_ids = fields.Many2many('sale.order', 
                                "stock_picking_sale_order_rel",   
                                "sale_id", 
                                "pick_id", string="Sale(s)")

    ## sale_id = fields.Many2one('sale.order', related='' ,string="Sale Order")
    sale_ids_count = fields.Integer(compute=compute_sale_ids_count)

    @api.multi
    def action_view_sale_order(self):
        
        self.ensure_one()#action = super().action_view_sale_order()
        action = self.env.ref('sale.action_orders').read()[0]
        form = self.env.ref('sale.view_order_form')
        tree = self.env.ref('sale.view_order_tree')
        action['views'] = [(tree.id, 'tree'), (form.id, 'form')]
        if len(self)== 1:
            action['res_id'] = self.sale_id.id
            action['views'] = [(form.id, 'form')]
        else:
            action['domain'] = [('id', 'in', self.sale_ids.ids)]
        return action
        """This function returns an action that display existing sales order
        of given picking.
        """
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        form = self.env.ref('sale.view_order_form')
        action['views'] = [(form.id, 'form')]
        action['res_id'] = self.sale_id.id
        return action
