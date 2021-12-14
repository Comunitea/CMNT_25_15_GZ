# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

import logging
_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    _inherit = "stock.location"

    @api.depends ('location_id', 'serial_location')
    def _compute_serial_location(self):
        
        for loc in self:
            location_id = loc
            serial_location = self.env['stock.location']
            while location_id and not location_id.serial_location:
                if location_id.serial_location:
                    loc.serial_location = location_id
                location_id = location_id.location_id

    serial_location = fields.Many2one('stock.location', string='Ubicación de nº serie', compute=_compute_serial_location)



