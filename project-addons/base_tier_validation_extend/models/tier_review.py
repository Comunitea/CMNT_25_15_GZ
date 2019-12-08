# Copyright 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TierReview(models.Model):
    _inherit = "tier.review"

    has_comment = fields.Boolean(
        related='definition_id.has_comment',
        readonly=True,
    )
    comment = fields.Char(
        string='Comments',
    )
    approve_sequence = fields.Boolean(
        related='definition_id.approve_sequence',
        readonly=True,
    )
