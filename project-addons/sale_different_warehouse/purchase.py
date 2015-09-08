# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2013 Pexego Sistemas Informáticos All Rights Reserved
#    $Santi Argüeso$ <santiago@pexego.es>
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
from openerp.osv import orm, fields


class purchase_order(orm.Model):

    _inherit = 'purchase.order'

    def _prepare_order_picking(self, cr, uid, order, context=None):
        res = super(purchase_order, self)._prepare_order_picking(cr, uid,
                                                                    order,
                                                                    context=context)
        res.update({'warehouse_id':order.warehouse_id.id})

        return res


class procurement_order(orm.Model):
    _inherit = 'procurement.order'


    def create_procurement_purchase_order(self, cr, uid, procurement, po_vals, line_vals, context=None):
        """Create the purchase order from the procurement, using
           the provided field values, after adding the given purchase
           order line in the purchase order.

           :params procurement: the procurement object generating the purchase order
           :params dict po_vals: field values for the new purchase order (the
                                 ``order_line`` field will be overwritten with one
                                 single line, as passed in ``line_vals``).
           :params dict line_vals: field values of the single purchase order line that
                                   the purchase order will contain.
           :return: id of the newly created purchase order
           :rtype: int
        """

        warehouse_pool = self.pool.get('stock.warehouse')
        location_pool = self.pool.get('stock.location')
        warehouse_ids = warehouse_pool.search(cr,uid,[])
        warehouse_id=False

        for warehouse in warehouse_pool.browse (cr,uid, warehouse_ids):
            if po_vals['location_id'] == warehouse.lot_stock_id.id or po_vals['location_id'] in location_pool._get_sublocations(cr, uid, warehouse.lot_stock_id.id, context=context):
               warehouse_id = warehouse.id

        po_vals['warehouse_id'] = warehouse_id
        return super(procurement_order, self).create_procurement_purchase_order(cr, uid,
                                                                    procurement, po_vals,
                                                                    line_vals,
                                                                    context=context)




