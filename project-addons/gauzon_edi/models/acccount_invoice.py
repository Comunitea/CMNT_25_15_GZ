# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    num_contract = fields.Char("Contract Number", size=128)
    note = fields.Text("Notes")
    edi_docs = fields.One2many("edi.doc", "invoice_id", "Documentos EDI")
    gi_cab_nodo = fields.Selection(
        [("380", "Comercial"), ("381", "Nota de crédito"), ("383", "Nota de débito")],
        "Nodo",
        default="380",
    )
    gi_cab_funcion = fields.Selection(
        [("9", "Original"), ("7", "Duplicado"), ("31", "Copia"), ("5", "Remplazo")],
        "Funcion",
        default="9",
    )

    @api.model
    def _get_refund_prepare_fields(self):
        res = super()._get_refund_prepare_fields()
        res.extend(["num_contract", "note"])
        return res
