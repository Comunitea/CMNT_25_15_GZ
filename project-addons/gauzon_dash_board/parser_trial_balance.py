# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2012 Pexego Sistemas Informáticos All Rights Reserved
#    $Javier Colmenero Fernández$ <javier@pexego.es>
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
#TODO: Migrar
# ~ from openerp.report import report_sxw
# ~ from openerp.report.report_sxw import rml_parse
# ~ import calendar
# ~ import itertools

# ~ class Parser(report_sxw.rml_parse):
    # ~ """Parser"""
    # ~ def __init__(self, cr, uid, name, context):
        # ~ super(Parser, self).__init__(cr,uid,name,context)
        # ~ self.localcontext.update({
            # ~ 'get_accounts': self._get_acocunts,
            # ~ 'get_balance_by_month' : self._get_balance_by_month,
            # ~ 'get_balance_last_year': self._get_balance_last_year
            # ~ })

    # ~ def _get_balance_last_year(self, account_data):
        # ~ fiscalyear = self.pool.get('account.fiscalyear').browse(self.cr, self.uid, self.localcontext['data']['form']['fiscalyear'][0])
        # ~ year = int(fiscalyear.code)
        # ~ last_fiscalyear_ids = self.pool.get('account.fiscalyear').search(self.cr, self.uid, [('code', '=', str(year-1))])
        # ~ if last_fiscalyear_ids:
            # ~ account = self.pool.get('account.account').browse(self.cr, self.uid, account_data[0].id, {'fiscalyear': last_fiscalyear_ids[0],
                                             # ~ 'business_lines': [account_data[1].id]})
            # ~ return account.balance
        # ~ else:
            # ~ return 0.0

    # ~ def _get_acocunts(self):
        # ~ wiz_account_ids = self.localcontext['data']['form']['account_list']
        # ~ account_ids = self.pool.get('account.account').search(self.cr,self.uid,[('id', 'child_of', wiz_account_ids), ('level', '=', 3)])
        # ~ account_ids = self.pool.get('account.account').browse(self.cr, self.uid, account_ids)

        # ~ wiz_bline_ids = self.localcontext['data']['form']['business_line_ids']
        # ~ bline_ids = self.pool.get('account.business.line').browse(self.cr, self.uid, wiz_bline_ids)

        # ~ return [x for x in itertools.product(account_ids, bline_ids)]

    # ~ def _get_balance_by_month(self, month, account_data):
        # ~ fiscalyear = self.pool.get('account.fiscalyear').browse(self.cr, self.uid, self.localcontext['data']['form']['fiscalyear'][0])
        # ~ year = int(fiscalyear.code)
        # ~ x, last_day = calendar.monthrange(year, month)

        # ~ account = self.pool.get('account.account').browse(self.cr, self.uid, account_data[0].id, {'fiscalyear': fiscalyear.id,
                                                                                        # ~ 'date_from': str(year) + "-01-01",
                                                                                         # ~ 'date_to': str(year) + "-" + str(month).zfill(2) + "-" + str(last_day),
                                                                                         # ~ 'business_lines': [account_data[1].id]})
        # ~ return account.balance



