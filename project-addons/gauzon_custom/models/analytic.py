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
from odoo import models, api


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        account_data = super().name_search(name, args=args, operator=operator,
                                           limit=limit)
        account_ids = [x[0] for x in account_data]
        account_childof_ids = self.search([('id', 'child_of', account_ids)])
        return account_childof_ids.name_get()
