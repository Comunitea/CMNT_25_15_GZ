# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductUom(models.Model):

    _inherit = "product.uom"

    edi_code = fields.Char("Codigo edi", size=64)


class ProductProduct(models.Model):

    _inherit = "product.product"

    ean13v = fields.Char("EAN13v", size=80)
    refcli = fields.Char("Ref. Cliente", size=80)
    refprov = fields.Char("Ref. Proveedor", size=80)

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        if not args:
            args = []
        recs = self.browse()
        if name:
            recs = self.search([("refcli", operator, name)])
            recs |= self.search([("refprov", operator, name)])

        if not recs:
            return super().name_search(name, args=args, operator=operator, limit=limit)
        else:
            records = super().name_search(
                name, args=args, operator=operator, limit=limit
            )
            records = [x[0] for x in records]
            records = self.browse(records)
            recs |= records
            return recs.name_get()


class ProductTemplate(models.Model):

    _inherit = "product.template"

    refcli = fields.Char("Ref. Cliente", related="product_variant_ids.refcli")
    refprov = fields.Char("Ref. Proveedor", related="product_variant_ids.refprov")
