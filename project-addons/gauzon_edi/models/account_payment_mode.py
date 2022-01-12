# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountPaymentMode(models.Model):

    _inherit = "account.payment.mode"

    edi_code = fields.Selection(
        [
            ("42", "A una cuenta bancaria"),
            ("14E", "Giro bancario"),
            ("10", "En efectivo"),
            ("20", "Cheque"),
            ("60", "Pagaré"),
        ],
        "Codigo EDI",
        index=1,
    )
