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
    def action_numbering(self):
        for purchase in self:
            cont = 1
            order_lines = self.env['purchase.order.line'].\
                search([('order_id', '=', purchase.id)], order="id asc")
            for line in order_lines:
                line.write({'sequence': cont})
                moves = self.env['stock.move'].\
                    search([('purchase_line_id', '=', line.id)])
                if moves:
                    moves.write({'sequence': cont})
                cont += 1

        return True


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking)
        if res:
            res[0]['sequence'] = self.sequence
        return res
