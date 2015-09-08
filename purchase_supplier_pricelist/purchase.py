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

from openerp.osv import orm


class purchase_order_line(orm.Model):

    _inherit = "purchase.order.line"

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context=None):
        """
        onchange handler of product_id.
        """
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order=date_order,fiscal_position_id=fiscal_position_id,
                                                              date_planned=date_planned,name=name,price_unit=price_unit,notes=notes,context=context)
        if product_id and partner_id and date_order:
            sinfo_ids = self.pool.get('product.supplierinfo').search(cr, uid, [('product_id', '=', product_id),('name','=',partner_id)])
            if sinfo_ids:
                pricelist_ids = self.pool.get('pricelist.partnerinfo').search(cr, uid, [('suppinfo_id', 'in', sinfo_ids),('min_quantity','<=',qty),('from_date','<=',date_order)], order="min_quantity DESC, from_date DESC", limit=1)
                if pricelist_ids:
                    pricelist = self.pool.get('pricelist.partnerinfo').browse(cr, uid, pricelist_ids[0])
                    res['value']['price_unit'] = (pricelist.gross_amount or pricelist.price)
                    res['value']['discount'] = pricelist.discount

        return res

