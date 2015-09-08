# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 Acysos SL. All Rights Reserved.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
import time
from openerp.tools import config

class account_account(orm.Model):
    _name = 'account.account'
    _inherit = 'account.account'

    def balance_calculation(self, cr, uid, ids, context, date=time.strftime('%Y-%m-%d'), periods=[]):
        acc_set = ",".join(map(str, ids))
        query = self.pool.get('account.move.line')._query_get(cr, uid,
                context=context)

        if not periods:
            cr.execute(("SELECT a.id, " \
                    "COALESCE(SUM(l.debit - l.credit), 0) " \
                "FROM account_account a " \
                    "LEFT JOIN account_move_line l " \
                    "ON (a.id=l.account_id) " \
                "WHERE a.type != 'view' " \
                    "AND a.id IN (%s) " \
                    "AND " + query + " " \
                    "AND a.active " \
                    "AND l.date <= '%s' "
                "GROUP BY a.id") % (acc_set, date))
        else:
            cr.execute(("SELECT a.id, " \
                    "COALESCE(SUM(l.debit - l.credit), 0) " \
                "FROM account_account a " \
                    "LEFT JOIN account_move_line l " \
                    "ON (a.id=l.account_id) " \
                "WHERE a.type != 'view' " \
                    "AND a.id IN (%s) " \
                    "AND " + query + " " \
                    "AND a.active " \
                    "AND l.period_id in (%s) " \
                "GROUP BY a.id") % (acc_set, ",".join(map(str, periods))))

        res = {}
        for account_id, sum in cr.fetchall():
            res[account_id] = round(sum,2)
        for id in ids:
            res[id] = round(res.get(id,0.0), 2)
        return res

class account_regularization(orm.Model):
    _name = 'account.regularization'
    _description = 'Account Regularization Model'
    _columns ={
        'name': fields.char('Name', size=32, required=True),
        'account_ids': fields.many2many('account.account', 'account_regularization_rel', 'regularization_id', 'account_id', 'Accounts to balance', required=True, domain=[('type','=','view')]),
        'debit_account_id': fields.many2one('account.account', 'Result account, debit', required=True),
        'credit_account_id': fields.many2one('account.account', 'Result account, credit', required=True),
        'balance_calc': fields.selection([('date','Date'),('period','Periods')], 'Regularization time calculation', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'move_ids': fields.one2many('account.move', 'regularization_id', 'Regularization Moves'),
    }

    _defaults = {
        'balance_calc': lambda *a: 'period',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid).company_id.id
    }


    def regularize(self, cr, uid, id, context, date=time.strftime('%Y-%m-%d'), period=None, journal=None, date_to=None, period_ids=[]):
        """ This method will calculate all the balances from all the child accounts of the regularization
        and create the corresponding move."""
        assert len(id)==1, "One regularization at a time"
        if not period or not journal:
            raise orm.except_orm('No period or journal defined')
        regularization = self.browse(cr,uid, id)[0]
        # Find all children accounts
        account_ids = self.pool.get('account.account')._get_children_and_consol(cr, uid, [x.id for x in regularization.account_ids], context)
        if date_to:
            balance_results = self.pool.get('account.account').balance_calculation(cr, uid, account_ids, context, date=date_to)
        else:
            balance_results = self.pool.get('account.account').balance_calculation(cr, uid, account_ids, context, periods=period_ids)
        if balance_results.keys().__len__() == balance_results.values().count(0.0):
            raise orm.except_orm('Nothing to regularize', 'Nothing to regularize')
        move = self.pool.get('account.move').create(cr, uid, {'journal_id': journal, 'period_id': period, 'regularization_id': regularization.id, 'date': date}, context=context)
        sum = 0.0
        for item in balance_results.keys():
            if balance_results[item] <> 0.0:
                val = {
                    'name': regularization.name,
                    'date': date,
                    'move_id': move,
                    'account_id':item,
                    'credit': ((balance_results[item]>0.0) and balance_results[item]) or 0.0,
                    'debit': ((balance_results[item]<0.0) and -balance_results[item]) or 0.0,
                    'journal_id': journal,
                    'period_id': period,
                }
                sum += balance_results[item]
                self.pool.get('account.move.line').create(cr, uid, val, context=context)
        diff_line = {
                    'name': regularization.name,
                    'date': date,
                    'move_id': move,
                    'account_id': (sum>0) and regularization.debit_account_id.id or regularization.credit_account_id.id,
                    'credit': ((sum<0.0) and -sum) or 0.0,
                    'debit': ((sum>0.0) and sum) or 0.0,
                    'journal_id': journal,
                    'period_id': period,
        }
        self.pool.get('account.move.line').create(cr, uid, diff_line, context=context)
        return


class account_move(orm.Model):
    _name = 'account.move'
    _inherit = 'account.move'
    _columns = {
        'regularization_id': fields.many2one('account.regularization', 'Regularization'),
    }


