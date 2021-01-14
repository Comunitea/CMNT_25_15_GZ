##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Kiko Sánchez$
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

from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_ids = fields.One2many(comodel_name='purchase.order', inverse_name="sale_id", string="Purchase Order", help="Purchase orders created from asociated purchase requistion")

    @api.multi
    def open_puchase_ids(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['domain'] = [('id', 'in', self.purchase_ids.ids)]
        return action

    @api.multi
    def action_cancel(self):
        domain =[('sale_id', 'in', self.ids), ('state', 'in', ['draft', 'in_progress', 'open'])]
        self.env['purchase.requisition'].search(domain).action_cancel()
        return super().action_cancel()

