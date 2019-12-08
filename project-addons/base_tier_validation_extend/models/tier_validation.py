# Copyright 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    has_comment = fields.Boolean(
        compute='_compute_has_comment',
    )
    approve_sequence = fields.Boolean(
        compute='_compute_approve_sequence',
    )

    @api.multi
    def _compute_approve_sequence(self):
        for rec in self:
            approve_sequence = rec.review_ids.filtered(
                lambda r: r.status in ('pending', 'rejected') and
                (self.env.user in r.reviewer_ids)).mapped('approve_sequence')
            rec.approve_sequence = True in approve_sequence

    @api.multi
    def _compute_has_comment(self):
        for rec in self:
            has_comment = rec.review_ids.filtered(
                lambda r: r.status in ('pending', 'rejected') and
                (self.env.user in r.reviewer_ids)).mapped('has_comment')
            rec.has_comment = True in has_comment

    @api.multi
    def _compute_can_review(self):
        for rec in self:
            rec.can_review = self.env.user in rec.reviewer_ids
            if rec.can_review and rec.approve_sequence:
                sequence = rec.review_ids.filtered(
                    lambda r: r.status in ('pending', 'rejected') and
                    (self.env.user in r.reviewer_ids)).mapped('sequence')
                sequence.sort()
                my_sequence = sequence[0]
                tier_bf = rec.review_ids.filtered(
                    lambda r: r.status != 'approved' and r.sequence <
                    my_sequence)
                if tier_bf:
                    rec.can_review = False

    def _add_comment(self, validate_reject):
        wizard = self.env.ref(
            'base_tier_validation_extend.view_comment_wizard')
        definition_ids = self.env['tier.definition'].search([
            ('model', '=', self._name),
            '|', ('reviewer_id', '=', self.env.user.id),
                 ('reviewer_group_id', 'in',
                  self.env.user.groups_id.ids)
        ])
        return {
            'name': _('Comment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'comment.wizard',
            'views': [(wizard.id, 'form')],
            'view_id': wizard.id,
            'target': 'new',
            'context': {
                'default_res_id': self.id,
                'default_res_model': self._name,
                'default_definition_ids': definition_ids.ids,
                'default_validate_reject': validate_reject
            },
        }

    @api.multi
    def validate_tier(self):
        self.ensure_one()
        if self.has_comment:
            return self._add_comment('validate')
        return super().validate_tier()

    @api.multi
    def reject_tier(self):
        self.ensure_one()
        if self.has_comment:
            return self._add_comment('reject')
        self._rejected_tier()
        self._update_counter()

    def _rejected_tier(self, tiers=False):
        self.ensure_one()
        tier_reviews = tiers or self.review_ids
        user_reviews = tier_reviews.filtered(
            lambda r: r.status in ('pending', 'approved') and
            (r.reviewer_id == self.env.user or
             r.reviewer_group_id in self.env.user.groups_id))
        user_reviews.write({
            'status': 'rejected',
            'done_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })
        for review in user_reviews:
            rec = self.env[review.model].browse(review.res_id)
            rec._notify_rejected_review()
