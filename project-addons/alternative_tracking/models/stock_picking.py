# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# from odoo.tools.float_utils import float_compare



_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def _get_move_line_grouped_count(self):
        for pick in self:
            pick.move_line_grouped_count = self.env["move.line.grouped"].search_count(
                [("picking_id", "=", pick.id)]
            )

    move_line_grouped_count = fields.Integer(compute="_get_move_line_grouped_count")

    def _compute_has_tracking(self):
        for picking in self:
            picking.has_tracking = any(
                (p.virtual_tracking or p.tracking != "none")
                for p in picking.move_lines.mapped("product_id")
            )

    def action_view_stock_move_lines_grouped(self):
        action = self.env.ref("alternative_tracking.move_line_grouped_action").read()[0]
        # action['view_mode'] = 'form'
        # del action['views']
        # del action['view_id']
        action["context"] = {}
        action["domain"] = [("picking_id", "=", self.id)]
        return action

    def _compute_virtual_tracking(self):
        return any(m.virtual_tracking for m in self.move_lines)

    @api.depends("picking_type_id.show_operations", "move_lines.product_id")
    def _compute_show_operations(self):
        if len(self) == 1 and self.state == "confirmed":
            if self.move_lines.filtered(lambda x: x.track_from_line):
                self.show_operations = True
                return
        return super()._compute_show_operations()
