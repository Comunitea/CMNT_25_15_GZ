# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2012 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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

class sale_order_line(orm.Model):

    _inherit = 'sale.order.line'
    _columns = {
        'warehouse_id': fields.many2one('stock.warehouse', 'Source warehouse', readonly=True, states={'draft': [('readonly', False)]}),
        'method': fields.selection(
                    [('direct_delivery', 'Direct delivery')],
                    string='Method',
                    readonly=True,
                    states={'draft': [('readonly', False)]}),
    }
    _defaults = {
        'method': 'direct_delivery'
    }


class sale_order(orm.Model):

    _inherit = 'sale.order'

    _columns = {
        'force_warehouse_id': fields.many2one('stock.warehouse', 'Force warehouse', help="This warehouse is entered by default for new lines")
    }

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, group_id, context=None):
        res = super(sale_order,self)._prepare_order_line_move(cr, uid, order, line, picking_id, group_id, context=context)
        if line.warehouse_id and line.method == 'direct_delivery':
            res['location_id'] = line.warehouse_id.lot_stock_id.id
            res['location_dest_id'] = line.warehouse_id.lot_output_id.id
            if res.get('picking_id', False) and not self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context).warehouse_id:
                self.pool.get('stock.picking').write(cr, uid, picking_id, {'warehouse_id': line.warehouse_id.id})
        else:
            if res.get('picking_id', False) and not self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context).warehouse_id:
                self.pool.get('stock.picking').write(cr, uid, picking_id, {'warehouse_id': order.shop_id.warehouse_id.id})

        return res

    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        res = super(sale_order,self)._prepare_order_line_procurement(cr, uid, order, line, group_id, context=context)
        if line.warehouse_id and line.method == 'direct_delivery':
            res['location_id'] = line.warehouse_id.lot_stock_id.id
        return res

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """
        Create so many pickings as different warehouses
        have between all the lines of a sale.

        :param browse_record order: sale order to which the order lines belong
        :param list(browse_record) order_lines: sale order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """
        warehouses = {}

        for line in order_lines:
            if line.warehouse_id and line.method == 'direct_delivery':
                if warehouses.get(line.warehouse_id):
                    warehouses[line.warehouse_id].append(line)
                else:
                    warehouses[line.warehouse_id] = []
                    warehouses[line.warehouse_id].append(line)
            else:
                if warehouses.get('default'):
                    warehouses['default'].append(line)
                else:
                    warehouses['default'] = []
                    warehouses['default'].append(line)

        for warehouse_line in warehouses:

            super(sale_order, self)._create_pickings_and_procurements(cr, uid,
                                                                    order,
                                                                    warehouses[warehouse_line],
                                                                    picking_id=False,
                                                                    context=None)

        return True

