# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# from odoo.tools.float_utils import float_compare
import logging

from odoo import _, api, fields, models
# from odoo.exceptions import ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

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


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    @api.multi
    def _is_bom_track(self):
        if not self._context.get("product_id"):
            return

        product_id = self._context["product_id"]
        for p_id in self.filtered(lambda x: x.product_id.id != product_id):
            p_id.is_bom_track = True

    # lot_name_ids = fields.One2many('move.lot.name', 'lot_id', string="Alternative tracking")
    virtual_tracking = fields.Boolean("Lot for alternative tracking", default=False)
    location_id = fields.Many2one("stock.location", "Location")
    move_ids = fields.One2many("stock.move", compute="_compute_tracking_moves")
    move_line_ids = fields.One2many(
        "stock.move.line", compute="_compute_tracking_moves"
    )
    is_bom_track = fields.Boolean(compute="_is_bom_track")

    def _compute_tracking_moves(self):
        domain = [("state", "=", "done"), ("lot_ids", "=", self.id)]
        self.move_line_ids = self.env["stock.move.line"].search(
            domain, order="date asc"
        )
        self.move_ids = self.move_line_ids.mapped("move_id")

    @api.model
    def get_available_lot_ids(self, location_id=False, product_id=False):
        domain = self.get_domain_for_available_lot_ids(location_id=location_id, product_ids=product_id)
        return self.search(domain)

    def get_domain_for_available_lot_ids(
        self, location_id=False, product_ids=False, strict=False, bom=True
    ):
        ## domain for virtual_tracking
        product_domain = []
        rest_domain = []
        tracking_domain = quant_domain = [("id", "=", False)]
        if product_ids:
            product_domain = [("product_id", "in", product_ids.ids)]
        else:
            product_domain = [("product_id.virtual_tracking", "=", True)]

        if location_id:
            if strict:
                operator = "="
            else:
                operator = "child_of"
            loc_domain = [("location_id", operator, location_id.id)]
            if location_id.usage not in ("internal", "view", "transit", "csutomer"):
                loc_domain = ["|", ("location_id", "=", False)] + loc_domain
        else:
            # Si hay ubicación, supongo solo lo que hay en stock (Internal)
            loc_domain = [("location_id.usage", "=", "internal")]

        res = [("virtual_tracking", "=", True)] + product_domain + loc_domain
        _logger.info(res)
        return res
"""
        if product_id and product_id.virtual_tracking or not product_id:
            tracking_domain = [("virtual_tracking", "=", True)]
            if product_id:
                product_domain = [("product_id", "=", product_id.id)]
            tracking_domain = expression.AND([tracking_domain, loc_domain])
            if product_id:
                tracking_domain = expression.AND([tracking_domain, product_domain])
                tracking_domain = expression.normalize_domain(tracking_domain)
        if product_id and not product_id.virtual_tracking or not product_id:
            quant_domain = [
                ("product_id.virtual_tracking", "=", False),
                ("lot_id", "!=", False),
                ("quantity", ">", 0),
            ] + loc_domain
            if product_id:
                quant_domain += product_domain
            res = (
                self.with_context({})
                .env["stock.quant"]
                .search_read(quant_domain, ["lot_id"])
            )
            ids = [x["lot_id"][0] for x in res]
            rest_domain = [("id", "in", ids)]
        domain = expression.OR([tracking_domain, rest_domain])
        print(domain)
        return domain

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):

        if self._context.get("available", False):
            d1 = self.get_domain_for_available_lot_ids()
            q_d = [
                ("lot_id", "!=", False),
                ("quantity", ">", 0),
                ("location_id.usage", "=", "internal"),
            ]
            q_ids = self.env["stock.quant"].search_read(q_d, ["lot_id"])

            d1 = expression.normalize_domain(d1)
            d2 = expression.normalize_domain(
                [
                    ("virtual_tracking", "=", False),
                    ("id", "in", [x["lot_id"][0] for x in q_ids]),
                ]
            )
            d = expression.OR([d1, d2])
            args = expression.normalize_domain(args)
            args = expression.AND([d, args])

        return super(StockProductionLot, self).search(
            args, offset=offset, limit=limit, order=order, count=count
        )
"""
