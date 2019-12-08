##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (httpw://www.comunitea.com)
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


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        if self.order_id.partner_id and self.product_id:
            customer_name = self.env['customer.product.name'].\
                search([('product_id', '=', self.product_id.id),
                        ('partner_id', '=', self.order_id.partner_id.id)],
                       limit=1)
            if customer_name:
                self.name = customer_name.name
        return res
