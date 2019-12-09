##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

from odoo import models, api


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    @api.multi
    def _add_supplier_to_product(self):
        return


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        res = super()._onchange_quantity()
        if not self.product_id:
            return res
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        if seller:
            price_unit = self.env['account.tax'].\
                _fix_tax_included_price_company(seller.gross_amount,
                                                self.product_id.
                                                supplier_taxes_id,
                                                self.taxes_id,
                                                self.company_id) if seller \
                else 0.0
            if price_unit and seller and self.order_id.currency_id and \
                    seller.currency_id != self.order_id.currency_id:
                price_unit = seller.currency_id.\
                    compute(price_unit, self.order_id.currency_id)

            if seller and self.product_uom and \
                    seller.product_uom != self.product_uom:
                price_unit = seller.product_uom.\
                    _compute_price(price_unit, self.product_uom)

            self.price_unit = price_unit
            self.discount = seller.discount or 0.0
        return res
