##############################################################################
#
#    Copyright (C) 2004-2011 Comunitea Servicios Tecnológicos S.L.
#    All Rights Reserved
#    $Santiago Argüeso Armesto$
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        res = super()._onchange_warehouse_id()
        if self.warehouse_id.analytic_account_id:
            self.analytic_account_id = self.warehouse_id.analytic_account_id.id

        return res

    @api.returns('self', lambda value: value.id)
    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        if default.get('unrevisioned_name'):
            default['analytic_account_id'] = self.analytic_account_id.id
        return super().copy(default=default)

    @api.multi
    def _action_confirm(self):
        super()._action_confirm()
        for order in self:
            if (not order.analytic_account_id and
                order.warehouse_id.analytic_account_id.id) or \
                    (order.analytic_account_id.name != order.name and
                     order.analytic_account_id.name !=
                     order.unrevisioned_name):
                if order.analytic_account_id:
                    parent_id = order.analytic_account_id.id
                else:
                    parent_id = order.warehouse_id.analytic_account_id.id
                order._create_analytic_account()
                order.refresh()
                if order.analytic_account_id and parent_id:
                    order.analytic_account_id.\
                            write({'parent_id': parent_id})
