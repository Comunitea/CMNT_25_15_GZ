# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# from odoo.tools.float_utils import float_compare


import logging
_logger = logging.getLogger(__name__)
"""
class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"


    @api.multi
    def _get_move_line_grouped_count(self):
        for batch in self:
            batch.move_line_grouped_count = self.env['move.line.grouped'].search_count([('batch_id', '=', batch.id)])

    move_line_grouped_count = fields.Integer (compute="_get_move_line_grouped_count")


    def action_view_stock_move_lines_grouped(self):
        action = self.env.ref('alternative_tracking.move_line_grouped_action').read()[0]
        # action['view_mode'] = 'kanban'
        # del action['views']
        # del action['view_id']
        # action['context']= {'groupby_location_dest_id':1}
        action['domain'] = [('batch_id', '=', self.id)]
        return action
    """