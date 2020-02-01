##############################################################################
#
#    Copyright (C) 2004-2014 Comunitea Servicios Tecnológios S.L.
#    All Rights Reserved
#    $Omar Castiñeira Saavedra$ <omar@pexego.es>
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


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def _amount_extra(self):
        for sale in self:
            val1 = val2 = 0.0
            for line in sale.order_line:
                if line.state != 'cancel':
                    val1 += line.price_subtotal
                    val2 += (line.price_unit * line.product_uom_qty)

            sale.amount_gross = round(val2, 2)
            sale.amount_discounted = round(val2 - val1, 2)

    amount_gross = fields.\
        Monetary(compute="_amount_extra", string='Amount gross')
    amount_discounted = fields.\
        Monetary(compute="_amount_extra", string='Discounted')


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super()._prepare_invoice_line(qty)
        res['sequence'] = self.sequence
        return res


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values, group_id):
        result = super()._get_stock_move_values(product_id, product_qty,
                                                product_uom, location_id, name,
                                                origin, values, group_id)
        if values.get('sale_line_id', False):
            line = self.env['sale.order.line'].browse(values['sale_line_id'])
            result['sequence'] = line.sequence
        return result
