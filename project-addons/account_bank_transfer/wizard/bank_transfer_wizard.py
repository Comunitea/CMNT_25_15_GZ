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

from odoo import models, fields
from odoo.addons import decimal_precision as dp
import time


class AccountBankTransferWzd(models.TransientModel):

    _name = "account.bank.transfer.wzd"

    orig_journal_id = fields.Many2one('account.journal', 'Orig. bank',
                                      required=True,
                                      domain=[('type', 'in',
                                               ['cash', 'bank'])])
    dest_journal_id = fields.Many2one('account.journal', 'Dest. bank',
                                      required=True,
                                      domain=[('type', 'in', ['cash',
                                                              'bank'])])
    amount = fields.Float('Amount to transfer',
                          digits=dp.get_precision('Account'), required=True)
    mid_account_id = fields.Many2one('account.account', 'Intermediate account',
                                     required=True)
    name = fields.Char('Description', size=64, required=True)
    date = fields.Date('Date', required=True, default=fields.Date.today)

    def execute_transfer(self, cr, uid, ids, context=None):
        if context is None: context = {}
        obj = self.browse(cr, uid, ids[0], context=context)
        context['account_period_prefer_normal'] = True
        period_id = self.pool.get('account.period').find(cr, uid, obj.date, context)[0]

        # orig account move
        orig_move_id = self.pool.get('account.move').create(cr, uid, {
            'ref': obj.name,
            'journal_id': obj.orig_journal_id.id,
            'date': obj.date,
            'period_id': period_id
        }, context=context)

        self.pool.get('account.move.line').create(cr, uid, {
            'move_id': orig_move_id,
            'name': obj.name,
            'ref': obj.name,
            'period_id': period_id,
            'journal_id': obj.orig_journal_id.id,
            'account_id': obj.orig_journal_id.default_credit_account_id.id,
            'credit': obj.amount,
            'date': obj.date
        }, context=context)
        self.pool.get('account.move.line').create(cr, uid, {
            'move_id': orig_move_id,
            'name': obj.name,
            'ref': obj.name,
            'period_id': period_id,
            'journal_id': obj.orig_journal_id.id,
            'account_id': obj.mid_account_id.id,
            'debit': obj.amount,
            'date': obj.date
        }, context=context)
        self.pool.get('account.move').button_validate(cr, uid, [orig_move_id], context=context)

        # dest account move
        dest_move_id = self.pool.get('account.move').create(cr, uid, {
            'ref': obj.name,
            'journal_id': obj.dest_journal_id.id,
            'date': obj.date,
            'period_id': period_id
        }, context=context)

        self.pool.get('account.move.line').create(cr, uid, {
            'move_id': dest_move_id,
            'name': obj.name,
            'ref': obj.name,
            'period_id': period_id,
            'journal_id': obj.dest_journal_id.id,
            'account_id': obj.dest_journal_id.default_debit_account_id.id,
            'debit': obj.amount,
            'date': obj.date
        }, context=context)
        self.pool.get('account.move.line').create(cr, uid, {
            'move_id': dest_move_id,
            'name': obj.name,
            'ref': obj.name,
            'period_id': period_id,
            'journal_id': obj.dest_journal_id.id,
            'account_id': obj.mid_account_id.id,
            'credit': obj.amount,
            'date': obj.date
        }, context=context)
        self.pool.get('account.move').button_validate(cr, uid, [dest_move_id], context=context)

        return {'type': 'ir.actions.act_window_close'}

