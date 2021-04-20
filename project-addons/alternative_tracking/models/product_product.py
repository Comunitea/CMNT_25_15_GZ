# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def _compute_tracking_count(self):
        for tmpl_id in self:
            tmpl_id.tracking_count = sum(x.tracking_count for x in tmpl_id.product_variant_ids)

    virtual_tracking = fields.Boolean(
        "With tracking", help="Alternative tracking for products with tracking = 'none'"
    )
    tracking_count = fields.Integer(
        "Tracking serial count", compute= _compute_tracking_count
    )

    @api.onchange("tracking")
    def onchange_tracking(self):
        self.virtual_tracking = False
        return super().onchange_tracking()

    @api.multi
    def action_view_serials(self):
        action = self.env.ref("stock.action_production_lot_form").read()[0]
        Stock = self.env['stock.warehouse'].search([])[0].lot_stock_id
        action["context"] = {"default_product_id": self.id, 'default_virtual_tracking': True, 'default_location_id': Stock.id}
        print (action['context'])
        domain = self.env["stock.production.lot"].get_domain_for_available_lot_ids(
            product_ids=self, bom=True
        )
        res = self.env["stock.production.lot"].search_read(domain, ["id"])
        if res:
            ids = [x["id"] for x in res]
            action["domain"] = [("id", "in", ids)]
        return action

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def _compute_tracking_count(self):
        for product_id in self:
            domain = self.env["stock.production.lot"].get_domain_for_available_lot_ids(
                product_ids=product_id, bom=True
            )
            product_id.tracking_count = self.env["stock.production.lot"].search_count(
                domain
            )

    tracking_count = fields.Integer(
        "Tracking serial count", compute=_compute_tracking_count
    )

    @api.multi
    def action_view_serials(self):
        action = self.env.ref("stock.action_production_lot_form").read()[0] 
        Stock = self.env['stock.warehouse'].search([])[0].lot_stock_id
        action["context"] = {"default_product_id": self.id, 'default_virtual_tracking': True, 'default_location_id': Stock.id}
        domain = self.env["stock.production.lot"].get_domain_for_available_lot_ids(
            product_ids=self, bom=True
        )
        res = self.env["stock.production.lot"].search_read(domain, ["id"])
        if res:
            ids = [x["id"] for x in res]
            action["domain"] = [("id", "in", ids)]
        return action

    def get_sub_product(self):
        bom_product_ids = self.env['product.product']
        for product in self:
            domain = [
                ("bom_id.product_tmpl_id", "=", product.product_tmpl_id.id),
                ("bom_id.product_tmpl_id.virtual_tracking", "=", True),
            ]
            bom_line_id = self.env["mrp.bom.line"].search(domain, limit=1)
            if bom_line_id:
                bom_product_ids |= bom_line_id.mapped("product_id")
        return self | bom_product_ids
