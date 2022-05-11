# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging


from odoo import api, fields, models, _

class StockPickingGroupAsign(models.TransientModel):
    _name = 'stock.picking.group.assign'

    picking_ids = fields.Many2many("stock.picking", string="Albaranes", domain = [('state', 'in', ['assigned', 'done'])])
    group_id = fields.Many2one("procurement.group", string="Abastecimiento")


    def _get_records(self, model):
        if self.env.context.get('active_domain'):
            records = model.search(self.env.context.get('active_domain'))
        elif self.env.context.get('active_ids'):
            records = model.browse(self.env.context.get('active_ids', []))
        else:
            records = model.browse(self.env.context.get('active_id', []))
        return records

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        active_model = self.env.context.get('active_model')
        model = self.env[active_model]
        records = self._get_records(model)
        result['picking_ids'] = records.ids
        return result

    @api.multi
    def action_apply_group(self):
        for pick in self.picking_ids:
            pick.group_id = self.group_id

            