from odoo.exceptions import ValidationError
from odoo import api, fields, models, _

class StockPickingGroupAsign(models.TransientModel):
    _name = 'stock.picking.group.assign'

    picking_ids = fields.Many2many("stock.picking", string="Albaranes", domain = [('state', 'in', ['assigned', 'done'])])
    group_id = fields.Many2one("procurement.group", string="Abastecimiento")
    old_group_id = fields.Many2one("procurement.group", readonly=True, string="Anterior ...")

    def _get_records(self, model):
        if self.env.context.get('active_ids'):
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
        if len(records) > 1:
            if any(x.picking_type_id.code == 'outgoing' for x in records):
                raise ValidationError ("No puedes asignar salidas en lote. Debes hacerlo uno a uno")
        if len(records) == 1 and records.group_id:
            result['old_group_id'] = records.group_id.id

        return result

    @api.multi
    def action_apply_group(self):
        for pick in self.picking_ids:
            pick.group_id = self.group_id

            