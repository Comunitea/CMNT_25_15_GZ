##############################################################################
#
#    Copyright (C) 2004-2012 Comunitea Servicios Tecnológicos S.L.
#    All Rights Reserved
#    $Omar Castiñeira Saavedra$ <omar@comuitea.com>
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
from odoo import models, fields, api


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    warehouse_id = fields.Many2one('stock.warehouse', 'Source warehouse',
                                   readonly=True,
                                   states={'draft': [('readonly', False)]})

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id=group_id)
        if self.warehouse_id:
            values['warehouse_id'] = self.warehouse_id

        return values
