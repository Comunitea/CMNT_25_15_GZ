##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
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

from odoo import models, fields, api


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    main_analytic_tag_id = fields.\
        Many2one('account.analytic.tag', 'Business line', readonly=True,
                 states={'draft': [('readonly', False)]},
                 domain=[('is_business_line', '=', True)])

    @api.model
    def invoice_line_move_line_get(self):
        lines = super().invoice_line_move_line_get()
        line_obj = self.env['account.invoice.line']
        for line_dict in lines:
            line = line_obj.browse(line_dict['invl_id'])
            if not line.analytic_tag_ids.filtered('is_business_line') and \
                    line.account_id.need_business_line and \
                    line.invoice_id.main_analytic_tag_id:
                line_dict['analytic_tag_ids'] = \
                    [(6, 0, [line.invoice_id.main_analytic_tag_id.id])]
        return lines

    def _get_refund_common_fields(self):
        field_list = super()._get_refund_common_fields()
        field_list.append('main_analytic_tag_id')
        return field_list


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    @api.model
    def default_get(self, default_fields):
        data = super().default_get(default_fields)
        if self.env.context.get('business_line'):
            data['analytic_tag_ids'] = \
                    [(6, 0, [self.env.context['business_line']])]

        return data
