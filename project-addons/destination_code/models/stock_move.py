##############################################################################
#
#    Copyright (C) 2020-TODAY
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

from odoo import models, fields

class StockMove(models.Model):

    _inherit = "stock.move"

    destination_code_id = fields.Many2one('res.partner', 'Destination code', domain=[('destination_code_id', '=', True)])
   
    def _get_new_picking_domain(self):
        domain = super()._get_new_picking_domain()
        if self.picking_type_id.code == 'outgoing' and self.destination_code_id:
            domain += [('destination_code_id', '=', self.destination_code_id.id)]
        return domain
    
    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        if self.destination_code_id:
            vals['destination_code_id'] = self.destination_code_id.id
        return vals
