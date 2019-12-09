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

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ProductSupplierInfo(models.Model):

    _inherit = 'product.supplierinfo'

    date_start = fields.Date(default=fields.Date.today)
    discount = fields.Float('Discount', digits=(4, 2), help="About 100")
    gross_amount = fields.Float('Gross unit amount',
                                digits=dp.get_precision('Product Price'))

    @api.onchange('gross_amount', 'discount')
    def on_change_price(self):
        self.price = self.gross_amount * (1 - (self.discount or 0.0) / 100.0)
