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


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    
    route_id = fields.Many2one('stock.location.route', string='Route')

    @api.multi
    def apply_route_id(self):
        for order in self:
            route_id = self.route_id and self.route_id.id or False
            order.order_line.write({'route_id': route_id})
    
