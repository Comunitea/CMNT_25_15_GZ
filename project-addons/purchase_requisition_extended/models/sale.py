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


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        
        return super()._prepare_procurement_values(group_id=group_id)
        values['sale_id'] = self.order_id.id
        return values


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _get_open_puchase_ids(self):
        for purchase in self:
            purchase.purchase_ids_count = len(purchase.purchase_ids)

    purchase_ids = fields.One2many(comodel_name='purchase.order', inverse_name="sale_id", string="Purchase Order", help="Purchase orders created from asociated purchase requistion")
    purchase_ids_count = fields.Integer(compute=_get_open_puchase_ids)
    requisition_id = fields.Many2one(related='procurement_group_id.requisition_id')
    
    @api.multi
    def open_puchase_ids(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['domain'] = [('id', 'in', self.purchase_ids.ids)]
        return action

    @api.multi
    def action_view_delivery(self):

        '''Heredo para añadir que agrupe por tipo de albarán"

        '''
        ctx = self._context.copy()
        ctx.update({'search_default_picking_type': True})
        action = super().action_view_delivery()
        action['context'] = ctx
        return action