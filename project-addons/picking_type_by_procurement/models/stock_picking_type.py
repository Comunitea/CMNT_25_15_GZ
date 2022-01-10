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
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    procurement_group_id = fields.Many2one('procurement.group', store=False, string="Procurement group")
    count_picking_done = fields.Integer(compute='_compute_picking_done')

    def _compute_picking_done(self):
        # TDE TODO count picking can be done using previous two
        if not self._context.get('procurement_group_id', False):
            self.write({'count_picking_done': 0})
            return
        domains = {
            'count_picking_done': [('state', '=', 'done')],
        }
        for field in domains:
            data = self.env['stock.picking'].read_group(domains[field], ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)
    
    def get_action_picking_tree_done(self):
        return self._get_action('stock.action_picking_tree_done')
    
    def _get_procurement_domain(self, procurement_group_id):
        picking_ids = self.env['stock.picking'].search([('group_id', '=', procurement_group_id)])
        ids = picking_ids.mapped('picking_type_id').ids
        return [('id', 'in', ids)] 
        
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self._context.get('procurement_group_id', False):
            domain = self._get_procurement_domain(self._context['procurement_group_id']) + domain
        return super(StockPickingType, self.with_context(virtual_id=False)).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def search_read(self, domain, fields, offset=0, limit=None, order=None):
        if self._context.get('procurement_group_id', False):
            domain = self._get_procurement_domain(self._context['procurement_group_id']) + domain
        return super(StockPickingType, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
