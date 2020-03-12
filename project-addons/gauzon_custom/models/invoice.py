##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
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

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):

    _inherit = "account.invoice"
    _order = 'id desc'

    name = fields.Char(size=64)
    origin = fields.Char(size=64)

    @api.multi
    def _check_duplicate_supplier_reference(self):
        for invoice in self:
            if invoice.type in ('in_invoice', 'in_refund') \
                    and invoice.reference:
                domain = [('type', '=', invoice.type),
                          ('reference', '=', invoice.reference),
                          ('company_id', '=', invoice.company_id.id),
                          ('commercial_partner_id', '=',
                           invoice.commercial_partner_id.id),
                          ('id', '!=', invoice.id)]
                if self.date_invoice:
                    year = self.date_invoice[:4]
                    domain.extend([('date_invoice', '>=', year + '-01-01'),
                                   ('date_invoice', '<=', year + '-12-31')])
                if self.search(domain):
                    raise UserError(_("Duplicated vendor reference detected. "
                                      "You probably encoded twice the same "
                                      "vendor bill/credit note."))

    @api.multi
    def write(self, vals):
        if 'date' in vals and not vals['date'] \
                and vals.get('state') == 'draft':
            del vals['date']
        return super().write(vals)

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        has_value = False
        if self.purchase_id and self.reference:
            old_ref = self.reference
            has_value = True
        res = super().purchase_order_change()
        if has_value:
            self.reference = old_ref
        else:
            self.reference = False
        return res
