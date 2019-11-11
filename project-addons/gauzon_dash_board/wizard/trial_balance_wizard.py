# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Pexego Sistemas Informáticos (http://www.pexego.es) All Rights Reserved
#    $Javier Colmenero Fernández$
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


class TrialBalanceWizard(models.TransientModel):

    _name = "trial.balance.wizard"

    company_id = fields.Many2one('res.company', 'Company', required=True)
    account_list = fields.\
        Many2many('account.account', 'wizard_trial_balance_rel', 'wizard_id',
                  'account_id', 'Root accounts', required=True)
    #TODO: Migrar'fiscalyear': fields.many2one('account.fiscalyear', 'Fiscal year', required=True),
    business_line_ids = fields.\
        Many2many('account.business.line',
                  'trial_balance_report_business_line_rel', 'wizard_id',
                  'bline_id', 'Business lines', required=True)

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = {}
        result = []
        if context and context.get('active_model') == 'account.account':
            list_ids = context.get('active_ids',[])
            if list_ids:
                res['account_list'] = [(6,0,list_ids)]
        res['company_id'] = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id
        res['fiscalyear'] = self.pool.get('account.fiscalyear').find(cr, uid)
        return res

    def export_trial_balance(self,cr,uid,ids,context):
        if context is None: context={}
        data = self.read(cr, uid, ids)[0]
        datas = {
             'ids': context.get('active_ids',[]),
             'model': 'trial.balance.wizard',
             'form': data
        }
        return {'type': 'ir.actions.report.xml',
                'report_name': 'trial_balance_report',
                'datas': datas,
                }

