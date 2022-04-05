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
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_is_zero, float_compare
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def update_to_new_warehouse(self)
        for pick in self:
            return pick.picking_type_id.update_to_new_warehouse(pick_domain = [('id', '=', pick.id)])

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'


    def get_equivalent_new_loc(self, new_wh_id, location_id):
        if self.code == 'incoming':
            location_id = new_wh_id.lot_stock_id
        if self.code == 'outgoing':
            location_id = new_wh_id.lot_stock_id

    @api.multi
    def reconfirm_sale_orders(self):
        domain = [('state', 'in', ['done', 'locked'])]
        

    @api.multi
    def update_to_new_warehouse(self, id=False, count=0, pick_domain = []):
        domain = [('code', 'in', ['incoming', 'outgoing'])]
        if id:
            domain +=[('id', '=', id)]
        for type_id in self.search(domain):
            if not pick_domain:
                pick_domain =[('picking_type_id', '=', type_id.id), ('state', 'in', ['draft', 'assigned', 'waiting'])]
            picking_ids = self.env['stock.picking'].search(pick_domain)
            new_wh_id = type_id.warehouse_id.parent_warehouse_id
            type_domain = [('warehouse_id', '=', new_wh_id.id), ('code', '=', type_id.code )]
            new_type_id = self.env['stock.picking.type'].search(type_domain, limit=1)
            if self.code == 'incoming':
                location_dest_id = new_wh_id.lot_stock_id
            if self.code == 'outgoing':
                location_id = new_wh_id.lot_stock_id
            if count>0:
                pick_ids = picking_ids[0:count]
            else:
                pick_ids = picking_ids
            for pick_id in pick_ids:
                _logger.info("MIGRANDO: %s"%pick_id.name)
                pick_id.move_line_ids.unlink()
                _logger.info(">>>: Estado: %s"%pick_id.state)
                _logger.info(">>> Cambiamos almacén a los movimientos: %s"%new_wh_id.name)
                pick_id.picking_type_id = new_type_id
                tag_ids = pick_id.move_lines.mapped('sale_line_id.order_id.analytic_tag_id')
                if not tag_ids:
                    tag_ids = pick_id.move_lines.mapped('product_id.analytic_tag_id')
                if tag_ids:
                    tag_id = tag_ids[0]
                else:
                    tag_id = False    
                vals = {}
                if type_id.code == 'incoming':
                    pick_id.location_dest_id = new_wh_id.lot_stock_id
                    vals = {'location_dest_id': new_wh_id.lot_stock_id.id}
                elif type_id.code == 'outgoing':
                    pick_id.location_id = new_wh_id.lot_stock_id
                    vals = {'location_id': new_wh_id.lot_stock_id.id}
                    
                elif type_id.code == 'mrp_operation':
                    vals = {'location_dest_id': new_wh_id.lot_stock_id.id,
                            'location_id': new_wh_id.lot_stock_id.id}
                elif type_id.code == 'internal':
                    pick_id.location_dest_id = new_wh_id.lot_stock_id
                    pick_id.location_id = new_wh_id.lot_stock_id
                    vals = {'location_dest_id': new_wh_id.lot_stock_id.id,
                            'location_id': new_wh_id.lot_stock_id.id}
                if tag_id:
                    vals['tag_id'] = tag_id
                vals['picking_type_id'] = new_type_id.id
                vals['warehouse_id'] = new_wh_id.id
                pick_id.move_lines.write(vals)
                pick_id.action_confirm()
                pick_id.action_assign()
                if tag_id and type_id.code == 'outgoing':
                    pick_id.move_lines.filtered(lambda x: not x.analytic_tag_id).write({'analytic_tag_id': tag_id.id})
                _logger.info(">>>: Estado: %s"%pick_id.state)

            self._cr.commit()

