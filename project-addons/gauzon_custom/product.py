# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-TODAY
#        Pexego Sistemas Informáticos (http://www.pexego.es) All Rights Reserved
#        $Javier Colmenero Fernández$
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
            if product.seller_ids:
                for supp in product.seller_ids:
                    if supp.product_code:
                        if not res:
                            res = supp.product_code
                        else:
                            res += (u", " + supp.product_code)
            product.supplier_codes = res

    def _search_bt_supp_code(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        ids = []
        supp_ids = self.pool.get('product.supplierinfo').search(cr, uid, [('product_code', args[0][1], args[0][2])])
        if supp_ids:
            ids = [x.product_tmpl_id.id for x in self.pool.get('product.supplierinfo').browse(cr, uid, supp_ids, context)]

        return [('id', 'in', list(set(ids)))]

    supplier_codes = fields.Text(compute="_get_supplier_codes",
                                 string="Supplier codes",
                                 search="_search_bt_supp_code")


class ProductProduct(models.Model):

    _inherit = "product.product"

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        ids = []
        if name:
            supp_ids = self.pool.get('product.supplierinfo').search(cr, user, [('product_code', operator, name)])
            if supp_ids:
                template_ids = [x.product_tmpl_id.id for x in self.pool.get('product.supplierinfo').browse(cr, user, supp_ids)]
                ids = self.search(cr, user, [('product_tmpl_id', 'in', template_ids)])

        if not ids:
            return super(ProductProduct, self).name_search(cr, user, name=name, args=args, operator=operator, context=context, limit=limit)
        else:
            records = super(ProductProduct, self).name_search(cr, user, name=name, args=args, operator=operator, context=context, limit=limit)
            new_ids = [x[0] for x in records]
            ids.extend(new_ids)
            ids = list(set(ids))
            return self.name_get(cr, user, ids, context=context)

