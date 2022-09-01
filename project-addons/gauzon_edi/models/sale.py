# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    edi_docs = fields.One2many("edi.doc", "sale_order_id", "Documento EDI", copy=False)
    order_type = fields.Selection(
        [("ORI", "ORI"), ("REP", "REP"), ("DEL", "DEL")], "Tipo", readonly=True
    )
    funcion_mode = fields.Selection(
        [
            ("0", "Aceptación ORDERS"),
            ("1", "Rechazo ORDERS"),
            ("2", "Oferta alternativa"),
            ("3", "Valoración ORDERS"),
        ],
        "Funcion",
        copy=False,
    )
    top_date = fields.Date("Fecha limite")
    urgent = fields.Boolean("Urgente")
    num_contract = fields.Char("Contract Number", size=128)
    partner_unor_id = fields.Many2one("res.partner", "UNOR EDI")

    def action_cancel(self):
        self.write({"funcion_mode": "1"})
        return super().action_cancel()

    @api.multi
    def _action_confirm(self):
        super()._action_confirm()
        self.write({"funcion_mode": "0"})

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals["num_contract"] = self.num_contract
        invoice_vals["note"] = self.note
        return invoice_vals

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        invoice_ids = super().action_invoice_create(grouped=grouped, final=final)
        for invoice in self.env["account.invoice"].browse(invoice_ids):
            orders = invoice.invoice_line_ids.mapped("sale_line_ids.order_id")
            if orders:
                invoice.note = ", ".join([x.note for x in orders.filtered("note")])
            num_contract = invoice.num_contract or ''
            for sale in orders:
                if sale.num_contract and sale.num_contract not in num_contract:
                    if not num_contract:
                        num_contract = sale.num_contract
                    else:
                        num_contract += ", " + sale.num_contract
            if num_contract and num_contract != invoice.num_contract:
                invoice.num_contract = num_contract

        return invoice_ids


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    refcli = fields.Char("Ref. Cliente", size=80)
    refprov = fields.Char("Ref. Proveedor", size=80)
    notes = fields.Text("Notas")

    @api.model
    def create(self, vals):
        if (
            vals.get("product_id", False)
            and not vals.get("refcli", False)
            and not vals.get("refprov", False)
        ):
            prod = self.env["product.product"].browse(vals["product_id"])
            vals.update({"refcli": prod.refcli, "refprov": prod.refprov})
        return super().create(vals)

    @api.multi
    def write(self, vals):
        for line in self:
            if vals.get("product_id", False):
                new_prod = self.env["product.product"].browse(vals["product_id"])
                if new_prod.id != line.product_id.id:
                    vals.update(
                        {"refcli": new_prod.refcli, "refprov": new_prod.refprov}
                    )
        return super().write(vals)
