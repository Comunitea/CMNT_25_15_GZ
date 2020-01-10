##############################################################################
#
#    Copyright (C) 2004-2014 Comunitea Servicios Tecnológicos S.L.
#    All Rights Reserved
#    $Omar Castiñeira Saavedra$ <omar@comunitea.com>
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

from odoo import models, fields, api


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    def _amount_extra(self):
        for invoice in self:
            val1 = val2 = 0.0
            for line in invoice.invoice_line_ids:
                val1 += line.price_subtotal
                val2 += (line.price_unit * line.quantity)

            invoice.amount_gross = round(val2, 2)
            invoice.amount_discounted = round(val2 - val1, 2)

    amount_gross = fields.Monetary(compute="_amount_extra",
                                   string='Amount gross')
    amount_discounted = fields.Monetary(compute="_amount_extra",
                                        string='Discounted')

    def _prepare_invoice_line_from_po_line(self, line):
        res = super()._prepare_invoice_line_from_po_line(line)
        res['sequence'] = line.sequence
        return res
