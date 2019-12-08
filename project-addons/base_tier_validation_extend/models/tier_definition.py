# Copyright 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TierDefinition(models.Model):
    _inherit = "tier.definition"

    has_comment = fields.Boolean(
        string='Comment',
        default=False,
    )
    approve_sequence = fields.Boolean(
        string='Approve by sequence',
        default=False,
        help="Approval order by the specified sequence number",
    )
