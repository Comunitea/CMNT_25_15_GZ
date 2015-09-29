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

class purchase_order_line(orm.Model):

    _inherit = "purchase.order.line"
    _order = "sequence asc"

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        data = super(purchase_order_line, self).default_get(cr, uid, fields, context=context)
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
                elif line_record[0] == 4:
                    line_record_detail = self.read(cr, uid, line_record[1], ['sequence'])
                elif line_record[0] == 0:
                    line_record_detail = line_record[2]
                else:
                    line_record_detail = False

                if line_record_detail and line_record_detail['sequence'] and line_record_detail['sequence'] >= sequence:
                    line_selected = line_record_detail
                    sequence = line_record_detail['sequence']

        data["sequence"] = sequence + 1

        return data

    _columns = {
        'sequence': fields.integer('Sequence', readonly=True, states={'draft':[('readonly',False)]})
    }


class purchase_order(orm.Model):

    _inherit = "purchase.order"

    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        if context is None: context = {}

        res = super(purchase_order, self)._prepare_inv_line(cr, uid, account_id, order_line, context=context)
        res['sequence'] = order_line.sequence

        return res

    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, group_id, context=None):
        if context is None: context = {}

        res = super(purchase_order, self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, group_id, context=context)
        for rec in res:
            rec['sequence'] = order_line.sequence

        return res

    def action_numbering(self, cr, uid, ids, context=None):
        if context is None: context = {}

        for purchase in self.browse(cr, uid, ids, context=context):
            cont = 1
            order_lines = self.pool.get('purchase.order.line').search(cr, uid, [('order_id', '=', purchase.id)], order="id asc")
            for line in order_lines:
                self.pool.get('purchase.order.line').write(cr, uid, [line], {'sequence': cont})
                move_ids = self.pool.get('stock.move').search(cr, uid, [('purchase_line_id', '=', line)])
                if move_ids:
                    self.pool.get('stock.move').write(cr, uid, move_ids, {'sequence': cont})
                cont += 1

        return True


class purchase_line_invoice(orm.TransientModel):

    _inherit = "purchase.order.line_invoice"

    def makeInvoices(self, cr, uid, ids, context=None):
        res = super(purchase_line_invoice, self).makeInvoices(cr, uid, ids, context=context)

        purchase_line_ids = context.get('active_ids', [])
        if purchase_line_ids:
            for line in self.pool.get('purchase.order.line').browse(cr, uid, purchase_line_ids):
                for invoice_line in line.invoice_lines:
                    invoice_line.write({'sequence': line.sequence})

        return res

