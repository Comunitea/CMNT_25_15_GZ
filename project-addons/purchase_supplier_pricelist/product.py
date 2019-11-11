# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Pexego Sistemas Informáticos (http://www.pexego.es) All Rights Reserved
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

#TODO: Migrar
# ~ class ProductSupplierinfo(models.Model):

    # ~ _inherit = "product.supplierinfo"

    # ~ @api.multi
    # ~ def _get_supplier_currency(self):
        # ~ for supp in self:
            # ~ supp.supplier_currency_id = \
                # ~ supp.name.property_product_pricelist_purchase and
                # ~ supp.name.property_product_pricelist_purchase.currency_id.id or False

        # ~ return res

    # ~ supplier_currency_id = fields.\
        # ~ Many2one("res.currency", compute="_get_supplier_currency",
                 # ~ string='Currency')


class ProductSupplierInfo(models.Model):

    _inherit = 'product.supplierinfo'

    from_date = fields.Date('From date', required=True,
                            default=fields.Date.today)
    discount = fields.Float('Discount', digits=(4, 2), help="About 100")
    gross_amount = fields.Float('Gross unit amount',
                                digits=dp.get_precision('Purchase Price'))

    def on_change_price(self, cr, uid, ids, gross_amount, discount):
        res = {'value': {'price': gross_amount * (1-(discount or 0.0)/100.0)}}
        return res

