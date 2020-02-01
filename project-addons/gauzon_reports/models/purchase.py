##############################################################################
#
#    Copyright (C) 2004-2014 Comunitea Servicios Tecnológicos S.L.
#    All Rights Reserved
#    $Omar Castiñeira Saavedra$ <omar@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from odoo import models, api


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @api.multi
    def _create_picking(self):
        res = super()._create_picking()
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in
                    order.order_line.mapped('product_id.type')]):
                picking = order.picking_ids.filtered(
                    lambda x: x.state not in ('done', 'cancel'))[0]
                for move in picking.move_lines:
                    if move.purchase_line_id:
                        move.write({'sequence':
                                    move.purchase_line_id.sequence})
        return res


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking)
        if res:
            res[0]['sequence'] = self.sequence
        return res
