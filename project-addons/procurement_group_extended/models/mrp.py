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


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def _adjust_procure_method(self):
        return super()._adjust_procure_method()
        
        routes = self.procurement_group_id.sale_id.route_id + self.procurement_group_id.sale_id.order_line.mapped('route_id')
        if routes:
            move = self.move_raw_ids[0]
            pull = self.env['procurement.rule'].search([
                ('route_id', 'in', [x.id for x in routes]), 
                ('location_src_id', '=', move.location_id.id),
                ('location_id', '=', move.location_dest_id.id),
                ('action', '=', 'product_default')], limit=1)
            if pull:
                for move in self.move_raw_ids:
                    move.procure_method = 'make_to_order'
                return True
        super()._adjust_procure_method()
    