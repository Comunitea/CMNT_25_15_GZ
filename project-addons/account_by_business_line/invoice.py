# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Pexego Sistemas Informáticos (http://www.pexego.es) All Rights Reserved
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

    business_line_id = fields.\
            Many2one('account.business.line', 'Business line', readonly=True,
                     states={'draft': [('readonly', False)]})

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res=super(AccountInvoice,self).line_get_convert(cr, uid, x, part, date, context=context)
        res['business_line_id'] = x.get('business_line_id', False)
        return res

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        vals = super(AccountInvoice, self)._prepare_refund(invoice, date=date,
                                                            period_id=period_id,
                                                            description=description,
                                                            journal_id=journal_id)
        vals["business_line_id"] = invoice.business_line_id.id
        return vals


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    business_line_id = fields.\
        Many2one('account.business.line', 'Business line',
                 default=lambda s: s.env.context.get('business_line', False))

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        data = super(AccountInvoiceLine, self).default_get(cr, uid, fields, context=context)
        if context.get('business_line', False):
            data['business_line_id'] = context['business_line']

        return data

    def move_line_get_item(self, cr, uid, line, context=None):
        res = super(AccountInvoiceLine, self).move_line_get_item(cr, uid, line, context=context)
        if res.get('account_id'):
            need_bussines_line = self.pool.get('account.account').browse(cr, uid, res['account_id']).need_business_line
            if need_bussines_line:
                res['business_line_id'] = line.business_line_id and line.business_line_id.id or (line.invoice_id.business_line_id and line.invoice_id.business_line_id.id or False)

        return res
