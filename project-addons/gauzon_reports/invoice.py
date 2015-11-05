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

class account_invoice(orm.Model):

    _inherit = "account.invoice"
    _order = "id desc"

    def _amount_extra(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for invoice in self.browse(cr, uid, ids):
            res[invoice.id] = {
                'amount_gross': 0.0,
                'amount_discounted': 0.0
            }
            val1 = val2 = 0.0
            for line in invoice.invoice_line:
                val1 += line.price_subtotal
                val2 += (line.price_unit * line.quantity)

            res[invoice.id]['amount_gross'] = round(val2, 2)
            res[invoice.id]['amount_discounted'] = round(val2 - val1, 2)

        return res

    _columns = {
        'amount_gross': fields.function(_amount_extra, method=True, digits_compute=dp.get_precision('Sale Price'), string='Amount gross', multi='extra', readonly=True),
        'amount_discounted': fields.function(_amount_extra, method=True, digits_compute=dp.get_precision('Sale Price'), string='Discounted', multi='extra', readonly=True),
    }


class account_invoice_line(orm.Model):

    _inherit = "account.invoice.line"
    _order = "picking_id asc, sequence asc"

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        data = super(account_invoice_line, self).default_get(cr, uid, fields, context=context)
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
        'sequence': fields.integer('Sequence'),
        'picking_id': fields.many2one('stock.picking', 'Picking', readonly=True)
    }

