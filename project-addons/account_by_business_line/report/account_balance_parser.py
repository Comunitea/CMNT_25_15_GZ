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

from account_financial_report.report import account_balance
from report import report_sxw

class new_account_balance(account_balance.account_balance):
    
    def lines(self, form, ids={}, done=None, level=0):
        if form.has_key('business_line_ids') and form['business_line_ids']:
            self.context['business_lines'] = form['business_line_ids']
        
        res = super(new_account_balance, self).lines(form, ids, done, level)
        return res

from netsvc import Service
del Service._services['report.account.balance.full.report.wzd'] 

report_sxw.report_sxw('report.account.balance.full.report.wzd', 'account.account', 'addons/account_financial_report/report/account_balance_full.rml', parser=new_account_balance, header=False)
