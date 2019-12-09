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

from odoo import models, fields, api


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def _get_sale_notes(self):
        for pick in self:
            sales = pick.move_lines.mapped('sale_line_id.order_id')
            pick.sale_note = sales and \
                "\n".join([x.note for x in sales if x.note]) or ""

    @api.multi
    def _amount_all(self):
        for picking in self:
            if not picking.sale_id:
                picking.amount_discounted = picking.amount_gross = 0.0
                continue
            amount_gross = 0.0
            for line in picking.move_lines:
                sale_line = line.sale_line_id
                if sale_line and line.state != 'cancel':
                    amount_gross += (line.sale_line_id.price_unit *
                                     line.product_qty)
                else:
                    continue
            round_curr = picking.sale_id.currency_id.round
            picking.amount_gross = round_curr(amount_gross)
            picking.amount_discounted = round_curr(amount_gross) - \
                picking.amount_untaxed

    sale_note = fields.Text(compute="_get_sale_notes", string='Sale notes')
    amount_gross = fields.Monetary('Amount gross', compute='_amount_all',
                                   compute_sudo=True)
    amount_discounted = fields.Monetary('Disounted amount',
                                        compute='_amount_all',
                                        compute_sudo=True)