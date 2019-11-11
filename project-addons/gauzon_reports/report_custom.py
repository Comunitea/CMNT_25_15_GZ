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

from odoo import models, fields, api


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    @api.multi
    def _get_taxes_str(self):
        for line in self:
            if line.tax_id:
                line.taxes_str = u",".join([x.name for x in line.tax_id])

    taxes_str = fields.Char(compute="_get_taxes_str", string="Taxes")


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.multi
    def _get_taxes_str(self):
        for line in self:
            if line.taxes_id:
                line.taxes_str = u",".join([x.name for x in line.taxes_id])

    taxes_str = fields.Char(compute="_get_taxes_str", string="Taxes")


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_tax_line(self):
        for move in self:
            if move.purchase_line_id and move.purchase_line_id.taxes_id:
                move.taxes_str = \
                    u', '.join(map(lambda x: x.name,
                                   move.purchase_line_id.taxes_id))
            elif move.sale_line_id and move.sale_line_id.tax_id:
                move.taxes_str = \
                    u', '.join(map(lambda x: x.name, move.sale_line_id.tax_id))

    taxes_str = fields.Char(compute="_get_tax_line", string="Tax line")

#TODO: Migrar
# ~ class AccountInvoice(models.Model):

    # ~ _inherit = 'account.invoice'

    # ~ def _get_move_lines_str(self, cr, uid, ids, field_name, args, context=None):
            # ~ """returns all move lines related to invoice in string"""

            # ~ if context is None: context = {};
            # ~ res = {}
            # ~ for invoice in self.browse(cr, uid, ids):
                # ~ expiration_dates_str = ""
                # ~ if invoice.move_id:
                    # ~ move_lines = [x.id for x in invoice.move_id.line_id]
                    # ~ move_lines = self.pool.get('account.move.line').search(cr, uid, [('id', 'in', move_lines)], order="date_maturity asc")
                    # ~ for line in self.pool.get('account.move.line').browse(cr, uid, move_lines):
                        # ~ if line.date_maturity:
                            # ~ date = time.strptime(line.date_maturity, "%Y-%m-%d")
                            # ~ date = datetime.fromtimestamp(mktime(date))
                            # ~ date = date.strftime("%d/%m/%Y")
                            # ~ if context.get('lang', False) and context['lang'] == 'es_ES':
                                # ~ expiration_dates_str += str(date) + "                          " + str(invoice.type in ('out_invoice','in_refund') and line.debit or (invoice.type in ('in_invoice','out_refund') and line.credit or 0)).replace('.', ',') + "\n"
                            # ~ else:
                                # ~ expiration_dates_str += str(date) + "                          " + str(invoice.type == 'out_invoice' and line.debit or (invoice.type == 'in_invoice' and line.credit or 0)) + "\n"

                # ~ res[invoice.id] = expiration_dates_str

            # ~ return res

    # ~ _columns = {
        # ~ 'expiration_dates_str': fields.function(_get_move_lines_str, string='Expiration dates', readonly=True, type="text"),
    # ~ }


class PaymentMode(models.Model):

    _inherit = "payment.mode"

    no_print = fields.Boolean("Not print")
