##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Javier Colmenero Fernández$
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


class ProductTemplate(models.Model):

    _inherit = "product.template"

    @api.multi
    def _get_supplier_codes(self):
        for product in self:
            res = ""
            for supp in product.seller_ids:
                if supp.product_code:
                    if not res:
                        res = supp.product_code
                    else:
                        res += (u", " + supp.product_code)
            product.supplier_codes = res

    def _search_bt_supp_code(self, operator, value):
        ids = []
        supps = self.env['product.supplierinfo'].\
            search([('product_code', operator, value)])
        if supps:
            ids = [x.product_tmpl_id.id for x in supps]

        return [('id', 'in', list(set(ids)))]

    supplier_codes = fields.Text(compute="_get_supplier_codes",
                                 string="Supplier codes",
                                 search="_search_bt_supp_code")


class ProductProduct(models.Model):

    _inherit = "product.product"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        recs = self.browse()
        if name:
            supps = self.env['product.supplierinfo'].\
                search([('product_code', operator, name)])
            if supps:
                recs = supps.mapped('product_tmpl_id.product_variant_ids')

        if not recs:
            return super().name_search(name, args=args, operator=operator,
                                       limit=limit)
        else:
            records = super().name_search(name, args=args, operator=operator,
                                          limit=limit)
            records = [x[0] for x in records]
            records = self.browse(records)
            recs += records
            return recs.name_get()
