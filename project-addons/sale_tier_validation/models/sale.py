# Copyright 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ['sale.order', 'tier.validation']
    _state_from = ['draft', 'sent']
    _state_to = ['sale']

    def _notify_accepted_reviews(self):
        if hasattr(self, 'message_post'):
            # Notify state change
            getattr(self, 'message_post')(
                subtype='mt_comment',
                body=self._notify_accepted_reviews_body()
            )

    def _notify_rejected_review(self):
        if hasattr(self, 'message_post'):
            # Notify state change
            getattr(self, 'message_post')(
                subtype='mt_comment',
                body=self._notify_rejected_review_body()
            )
