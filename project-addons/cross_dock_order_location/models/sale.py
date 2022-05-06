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

from odoo import models, fields, api, exceptions, _
from odoo.addons import decimal_precision as dp



class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"
    

    def _check_cross_docking_location(self, group_id):
        
        if not self.route_id:
            return False
        
        for rule_id in self.route_id.pull_ids:
            if rule_id.location_src_id.cross_dock:
                loc_name = group_id.name or self.order_id.name
                domain = [('quant_ids', '=', False), ('cross_dock', '=', True), '|', ('name', '=', loc_name), ('active', '=', False)]
                cross_dock_loc = self.env['stock.location'].sudo().search(domain,  limit=1, order="active desc")
                if cross_dock_loc:
                    if cross_dock_loc.name != loc_name:
                        cross_dock_loc.loc_name = loc_name
                        cross_dock_loc.active = True
                        ## Tengo que cambiar las traducciones
                        domain = [('name', '=', 'stock.location,name'), ('source', '=', loc_name)]
                        self.env['ir.translation'].search(domain).write({'value': loc_name})
                else:

                    vals = {
                        'location_id': rule_id.location_src_id.id, 
                        'name': loc_name, 
                        'removal_priority': 0,
                        'cross_dock': True}
                    cross_dock_loc = self.env['stock.location'].sudo().create(vals)
                return cross_dock_loc
        return False
                
    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        cross_dock_loc = self._check_cross_docking_location(group_id)
        vals = super()._prepare_procurement_values(group_id=group_id)

        return vals