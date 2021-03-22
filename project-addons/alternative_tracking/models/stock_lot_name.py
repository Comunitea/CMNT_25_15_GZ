# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

LOT_NAMES_TYPES = [
    ("supplier", "Vendor Location"),
    ("view", "View"),
    ("internal", "Internal Location"),
    ("customer", "Customer Location"),
    ("inventory", "Inventory Loss"),
    ("procurement", "Procurement"),
    ("production", "Production"),
    ("transit", "Transit Location"),
]

class StockLotName(models.Model):
    _name = "move.lot.name"

    name = fields.Char("Lot name")
    lot_id = fields.Many2one("stock.production.lot", "Lot")
    product_id = fields.Many2one("product.product", "Product")

    move_ids = fields.Many2many(
        comodel_name="stock.move",
        relation="lot_name_move_rel",
        column1="lot_name_id",
        column2="move_id",
        string="Move",
        copy=False,
    )

    usage = fields.Selection(LOT_NAMES_TYPES, "Usage")
    location_id = fields.Many2one("stock.location", "Location")

    def get_domain_for_available_lot_names(self, location_id=False, product_id=False):
        domain = []
        if location_id:
            domain += [("location_id", "=", location_id.id)]
        if product_id:
            domain += [("product_id", "=", product_id.id)]
        return domain

    @api.model
    def get_available_lot_names(self, location_id=False, product_id=False):
        domain = self.get_domain_for_available_lot_names(
            location_id=location_id, product_id=product_id
        )
        return self.search(domain)
