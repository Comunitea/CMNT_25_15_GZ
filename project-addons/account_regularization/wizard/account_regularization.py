# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 Acysos SL. All Rights Reserved.
#    Copyright (c) 2014 Pexego Sistemas Informáticos. All Rights Reserved.
#                       Omar Castiñeira Saavedra <omar@pexego.es>
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

from openerp.osv import orm, fields
import time

class wizard_regularize(orm.TransientModel):

    _name = "account.regularization.regularize"

    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal year', help="Fiscal Year for the write move", required=True),
        'journal_id': fields.many2one('account.journal', 'Journal', help="Journal for the move", required=True),
        'period_id': fields.many2one('account.period', 'Move Period', help="Period for the move", required=True),
        'date_move': fields.date('Date', help="Date for the move.", required=True),
        'period_ids': fields.many2many('account.period', 'account_regularization_regularize_period_rel', 'wzd_id', 'period_id', help="Periods to regularize", string="Periods"),
        'date_to': fields.date('Date to', help="Include movements up to this date"),
        'view_type': fields.selection([('dates', 'Dates'),('periods', 'Periods')], string="View_type", readonly=True)
    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = {}
        regu_type = self.pool.get('account.regularization').read(cr, uid, context['active_id'], ['balance_calc',])['balance_calc']
        if regu_type == 'date':
            res['view_type'] = 'dates'
        else:
            res['view_type'] = 'periods'
        res['fiscalyear_id'] = self.pool.get('account.fiscalyear').find(cr, uid)
        res['period_id'] = self.pool.get('account.period').find(cr, uid, dt=time.strftime('%Y-%m-%d'))[0]
        res['date_move'] = time.strftime('%Y-%m-%d')
        return res

    def action_regularize(self, cr, uid, ids, context=None):
        if context is None: context = {}
        regu_objs = self.pool.get('account.regularization').browse(cr, uid, context['active_ids'])
        obj = self.browse(cr, uid, ids[0])

        period_ids = [x.id for x in obj.period_ids]

        for regu in regu_objs:
            regu.regularize(context, obj.date_move, obj.period_id.id, obj.journal_id.id, obj.date_to, period_ids)

        return {'type': 'ir.actions.act_window_close'}

