# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra$ <omar@pexego.es>
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
import openerp.addons.decimal_precision as dp

class sale_order(orm.Model):

    _inherit = "sale.order"

    def _amount_extra(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for sale in self.browse(cr, uid, ids):
            res[sale.id] = {
                'amount_gross': 0.0,
                'amount_discounted': 0.0
            }
            val1 = val2 = 0.0
            for line in sale.order_line:
                if line.state != 'cancel':
                    val1 += line.price_subtotal
                    val2 += (line.price_unit * line.product_uom_qty)

            res[sale.id]['amount_gross'] = round(val2, 2)
            res[sale.id]['amount_discounted'] = round(val2 - val1, 2)

        return res

    _columns = {
        'amount_gross': fields.function(_amount_extra, method=True, digits_compute=dp.get_precision('Sale Price'), string='Amount gross', multi='extra', readonly=True),
        'amount_discounted': fields.function(_amount_extra, method=True, digits_compute=dp.get_precision('Sale Price'), string='Discounted', multi='extra', readonly=True),
    }

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        res = super(sale_order, self)._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context)
        res['sequence'] = line.sequence
        return res

    def action_numbering(self, cr, uid, ids, context=None):
        if context is None: context = {}

        for sale in self.browse(cr, uid, ids, context=context):
            cont = 1
            order_lines = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', sale.id)], order="id asc")
            for line in order_lines:
                self.pool.get('sale.order.line').write(cr, uid, [line], {'sequence': cont})
                move_ids = self.pool.get('stock.move').search(cr, uid, [('sale_line_id', '=', line)])
                if move_ids:
                    self.pool.get('stock.move').write(cr, uid, move_ids, {'sequence': cont})
                cont += 1

        return True


class sale_order_line(orm.Model):

    _inherit = "sale.order.line"
    _order = "sequence asc"

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        data = super(sale_order_line, self).default_get(cr, uid, fields, context=context)
        data2 = self._default_get(cr, uid, fields, context=context)
        data.update(data2)
        for f in data.keys():
            if f not in fields:
                del data[f]
        return data

    def _default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        data = {}
        sequence = 0

        if context.get('lines',[]):
            line_selected = False

            for line_record in context['lines']:
                if not isinstance(line_record, (tuple, list)):
                    line_record_detail = self.read(cr, uid, line_record, ['sequence'])
                else:
                    line_record_detail = line_record[2]

                if line_record_detail['sequence'] and line_record_detail['sequence'] >= sequence:
                    line_selected = line_record_detail
                    sequence = line_record_detail['sequence']

        data["sequence"] = sequence + 1

        return data

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        if context is None: context = {}

        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id=account_id, context=context)
        if isinstance(res, dict):
            res['sequence'] = line.sequence

        return res

