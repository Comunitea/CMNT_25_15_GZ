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

from openerp.osv import orm, fields


class product_template(orm.Model):

    _inherit = "product.template"

    def _get_supplier_codes(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context):
            res[product.id] = ""
            if product.seller_ids:
                for supp in product.seller_ids:
                    if supp.product_code:
                        if not res[product.id]:
                            res[product.id] = supp.product_code
                        else:
                            res[product.id] += (u", " + supp.product_code)
        return res

    def _search_bt_supp_code(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        ids = []
        supp_ids = self.pool.get('product.supplierinfo').search(cr, uid, [('product_code', args[0][1], args[0][2])])
        if supp_ids:
            ids = [x.product_tmpl_id.id for x in self.pool.get('product.supplierinfo').browse(cr, uid, supp_ids, context)]

        return [('id', 'in', list(set(ids)))]

    _columns = {
        'supplier_codes': fields.function(_get_supplier_codes, method=True, string="Supplier codes", fnct_search=_search_bt_supp_code, type="text", readonly=True)
    }


class product_product(orm.Model):

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
            return super(product_product, self).name_search(cr, user, name=name, args=args, operator=operator, context=context, limit=limit)
        else:
            records = super(product_product, self).name_search(cr, user, name=name, args=args, operator=operator, context=context, limit=limit)
            new_ids = [x[0] for x in records]
            ids.extend(new_ids)
            ids = list(set(ids))
            return self.name_get(cr, user, ids, context=context)

