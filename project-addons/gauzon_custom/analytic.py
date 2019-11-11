# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Informáticos All Rights Reserved
#    $Carlos Lombardía Rodríguez$
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
from odoo import models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        account_data = super(AccountAnalyticAccount, self).name_search(cr, uid, name, args=args, operator=operator, context=context, limit=limit)
        account_ids = [x[0] for x in account_data]
        account_childof_ids = self.search(cr, uid, [('id', 'child_of', account_ids)])
        account_childof_ids = list(set(account_childof_ids))
        return self.name_get(cr, uid, account_childof_ids, context=context)
