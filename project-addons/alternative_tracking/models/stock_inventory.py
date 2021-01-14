# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# from odoo.tools.float_utils import float_compare


class StockInventoryTracking(models.Model):
    _name = "stock.inventory.tracking"

    inventory_id = fields.Many2one(
        "stock.inventory", "Inventory", index=True, ondelete="cascade"
    )
    product_id = fields.Many2one(
        "product.product",
        "Product",
        domain=[("virtual_tracking", "=", True)],
        required=True,
    )
    location_id = fields.Many2one("stock.location", "Location", required=True)
    prod_lot_id = fields.Many2one(
        "stock.production.lot",
        "Lot/Serial Number",
        domain="[('product_id','=',product_id)]",
    )
    to_delete = fields.Boolean("To delete", default=False)
    lot_name = fields.Char("Lot name")

    @api.onchange("prod_lot_id")
    def onchange_prod_lot_id(self):
        self.lot_name = self.prod_lot_id.name

    def alternate_to_delete(self):
        self.ensure_one()
        self.to_delete = not self.to_delete


class Inventory(models.Model):
    _inherit = "stock.inventory"

    inventory_type = fields.Selection(
        selection=[("qty", "Quantity"), ("serial", "Serial")],
        string="Inventory Type",
        default="qty",
    )
    available_lot_ids = fields.One2many(
        "stock.inventory.tracking",
        "inventory_id",
        string="Serial Inventories",
        copy=False,
        readonly=False,
        states={"done": [("readonly", True)]},
    )

    def action_cancel_draft(self):
        self.available_lot_ids.unlink()
        return super().action_cancel_draft()

    def create_lines_vals(self, lines=False, inventory_location=False):

        # Miro las lineas y quito las que no impliquen movimientos
        lot_obj = self.env["stock.production.lot"]
        ctx = self._context.copy()
        lines_to_create = self.env["stock.inventory.tracking"]
        if not lines:
            return False
        for line in lines:
            domain = [
                ("virtual_tracking", "=", True),
                ("product_id", "=", line.product_id.id),
                ("location_id", "child_of", line.location_id.id),
            ]
            if line.to_delete:
                if not line.prod_lot_id:
                    raise ValidationError(_("Lines to delete need serial"))
                # solo puedo borrar lotes existentes
                domain_to_delete = domain + [("id", "=", line.prod_lot_id.id)]
                lot_id = lot_obj.search_read(domain_to_delete, ["name"], limit=1)
                if not lot_id:
                    ## Si ya no encuentro un lote aquí, la línea no hace nada
                    continue
            else:
                if not line.prod_lot_id and not line.lot_name:
                    raise ValidationError(_("Lines to add need serial"))
                # puedo añadirlas con lot_id o con name
                if line.prod_lot_id:
                    domain_to_add = domain + [("id", "=", line.prod_lot_id.id)]
                else:
                    domain_to_add = domain + [("name", "=", line.lot_name)]
                lot_id = lot_obj.search_read(domain_to_add, ["name"], limit=1)
                if lot_id:
                    # Si ya encuentro un lote aquí, la línea no hace nada
                    continue
            # Si llego aquí:
            lines_to_create |= line
        ctx = self._context.copy()
        ctx.update(bypass_run_validation=True)
        ctx.update(by_pass_compute_qties=True)
        while lines_to_create:
            line = lines_to_create[0]
            if line.to_delete:
                location_id = line.location_id
                location_dest_id = inventory_location
            else:
                location_dest_id = line.location_id
                location_id = inventory_location
            this_lines = lines_to_create.filtered(
                lambda x: x.product_id == line.product_id
                and x.location_id == line.location_id
                and x.to_delete == line.to_delete
            )

            lot_names = this_lines.filtered(
                lambda x: not x.prod_lot_id and x.lot_name
            ).mapped("lot_name")
            lot_names += this_lines.filtered(lambda x: x.prod_lot_id).mapped(
                "prod_lot_id.name"
            )
            lot_names = list(set(lot_names))
            move_vals = {
                "product_id": line.product_id.id,
                "location_id": location_id.id,
                "location_dest_id": location_dest_id.id,
                "product_uom_qty": 0,  # len(lot_names),
                "quantity_done": 0,
                "state": "done",
                "origin": self.name,
                "date": fields.Datetime.now(),
                "product_uom": line.product_id.uom_id.id,
                "inventory_id": self.id,
                "name": "{} - {}".format(self.name, line.product_id.display_name),
            }

            move_id = self.env["stock.move"].with_context(ctx).create(move_vals)
            sml_vals = move_id._prepare_move_line_vals()
            sml_vals["state"] = "done"
            move_id.move_line_ids.create(sml_vals)

            move_id.create_move_lots_from_list(lot_names, compute_qties=False)

            lines_to_create -= this_lines

    def action_validate(self):

        if self.inventory_type != "serial":
            return super().action_validate()
        self.ensure_one()
        inventory_location = self.env["stock.location"].search(
            [("usage", "=", "inventory")], limit=1
        )
        if not inventory_location:
            raise ValidationError(_("Inventory loss location not found"))
        if any(
            not x.virtual_tracking for x in self.available_lot_ids.mapped("product_id")
        ):
            raise ValidationError(_("Products with no tracking"))

        self.create_lines_vals(self.available_lot_ids, inventory_location)

        self.move_ids._action_done()
        self.write({"state": "done", "date": fields.Datetime.now()})

    def action_start_serial(self):
        for inventory in self.filtered(lambda x: x.state not in ("done", "cancel")):

            vals = {
                "state": "confirm",
                "date": fields.Datetime.now(),
                "inventory_type": "serial",
            }
            location_id = self.location_id
            product_id = self.product_id
            domain = [
                ("location_id", "child_of", location_id.id),
                ("virtual_tracking", "=", True),
            ]
            if product_id:
                domain += [("product_id", "=", product_id.id)]
                lot_ids = self.env["stock.production.lot"].search_read(
                    domain, ["id", "location_id", "product_id"], order="location_id asc"
                )
            else:
                domain = [
                    ("location_id", "child_of", location_id.id),
                    ("virtual_tracking", "=", True),
                ]
                lot_ids = self.env["stock.production.lot"].search_read(
                    domain, ["id", "location_id", "product_id"], order="product_id asc"
                )
            values = []
            for lot in lot_ids:
                lot_vals = {
                    "inventory_id": inventory.id,
                    "product_id": lot["product_id"][0],
                    "location_id": lot["location_id"][0],
                    "prod_lot_id": lot["id"],
                    "to_delete": False,
                }
                values.append(lot_vals)
            if values:
                vals.update(
                    {
                        "available_lot_ids": [
                            (0, 0, line_values) for line_values in values
                        ]
                    }
                )
            inventory.write(vals)
        return True
