# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011 Pexego Sistemas Informáticos. All Rights Reserved
#    $Javier Colmenero Fernández$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from time import mktime
import time
from datetime import datetime

class sale_order_line(orm.Model):

    _inherit = "sale.order.line"

    def _get_taxes_str(self, cr, uid, ids, field_name, arg, context=None):
        if context is None: context = {}
        res = {}
        for line in self.browse(cr, uid, ids):
            if line.tax_id:
                res[line.id] = u",".join([x.name for x in line.tax_id])
            else:
                res[line.id] = ""

        return  res

    _columns = {
        'taxes_str': fields.function(_get_taxes_str, method=True, string="Taxes", readonly=True, type="char", size=256),
    }



class purchase_order_line(orm.Model):

    _inherit = "purchase.order.line"

    def _get_taxes_str(self, cr, uid, ids, field_name, arg, context=None):
        if context is None: context = {}
        res = {}
        for line in self.browse(cr, uid, ids):
            if line.taxes_id:
                res[line.id] = u",".join([x.name for x in line.taxes_id])
            else:
                res[line.id] = ""

        return  res

    _columns = {
        'taxes_str': fields.function(_get_taxes_str, method=True, string="Taxes", readonly=True, type="char", size=256),
    }


class stock_move(orm.Model):
    _inherit = 'stock.move'

    def _get_tax_line(self, cr, uid, ids, field_name, arg, context=None):
        if context is None: context = {}
        res = {}
        for move in self.browse(cr, uid, ids):
            if move.purchase_line_id and move.purchase_line_id.taxes_id:
                res[move.id] = u', '.join(map(lambda x: x.name, move.purchase_line_id.taxes_id))
            elif move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.tax_id:
                res[move.id] = u', '.join(map(lambda x: x.name, move.procurement_id.sale_line_id.tax_id))
            else:
                res[move.id] = ""
        return res

    _columns = {
        'taxes_str': fields.function(_get_tax_line, method=True, string="Tax line", readonly=True, type="char", size=255),
    }


class account_invoice(orm.Model):

    _inherit = 'account.invoice'

    def _get_move_lines_str(self, cr, uid, ids, field_name, args, context=None):
            """returns all move lines related to invoice in string"""

            if context is None: context = {};
            res = {}
            for invoice in self.browse(cr, uid, ids):
                expiration_dates_str = ""
                if invoice.move_id:
                    move_lines = [x.id for x in invoice.move_id.line_id]
                    move_lines = self.pool.get('account.move.line').search(cr, uid, [('id', 'in', move_lines)], order="date_maturity asc")
                    for line in self.pool.get('account.move.line').browse(cr, uid, move_lines):
                        if line.date_maturity:
                            date = time.strptime(line.date_maturity, "%Y-%m-%d")
                            date = datetime.fromtimestamp(mktime(date))
                            date = date.strftime("%d/%m/%Y")
                            if context.get('lang', False) and context['lang'] == 'es_ES':
                                expiration_dates_str += str(date) + "                          " + str(invoice.type in ('out_invoice','in_refund') and line.debit or (invoice.type in ('in_invoice','out_refund') and line.credit or 0)).replace('.', ',') + "\n"
                            else:
                                expiration_dates_str += str(date) + "                          " + str(invoice.type == 'out_invoice' and line.debit or (invoice.type == 'in_invoice' and line.credit or 0)) + "\n"

                res[invoice.id] = expiration_dates_str

            return res

    _columns = {
        'expiration_dates_str': fields.function(_get_move_lines_str, string='Expiration dates', readonly=True, type="text"),
    }


class payment_mode(orm.Model):

    _inherit = "payment.mode"

    _columns = {
        'no_print': fields.boolean("Not print")
    }
