# Copyright 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TierReview(models.Model):
    _inherit = "tier.review"

    has_comment = fields.Boolean(
        compute='_compute_has_comment',
    )
    comment = fields.Char(
        string='Comments',
    )
    approve_sequence = fields.Boolean(
        compute='_compute_approve_sequence',
    )
