# -*- coding: utf-8 -*-
# Copyright 2018 Kiko Sánchez, <kiko@comunitea.com> Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

DOMAIN_NOT_STATE = ['draft', 'cancel']

class StockMove(models.Model):

    _inherit = "stock.move"

    sale_id = fields.Many2one('sale.order', 'Saler Order')

    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals['sale_id'] = self.sale_id.id
        return vals
    
    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        sale_id = self.sale_id and self.sale_id.id
        if sale_id:
            vals['sale_id'] = sale_id
            vals['sale_ids'] = [(6, 0, [sale_id])]
        return vals

    def _assign_picking_post_process(self, new=False):
        ### import pdb; pdb.set_trace()
        super()._assign_picking_post_process(new=new)
        if self.sale_id:
            self.picking_id.write({'sale_ids': [(4, self.sale_id.id)]})
        if len(self.picking_id.sale_ids) == 1:
            self.picking_id.sale_id = self.picking_id.sale_ids
        else:
            self.picking_id.sale_id = self.env['sale.order']

    
    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        # Esto nos permite que si así lo indicamos en el tipo de albarán, 
        # no mezcle los movimientos del picking ala ñadirlos alalbarán si son de distinta venta
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        if len(self) == 1:
            if not self.group_id.merge_moves and not self[0].picking_type_id.merge_moves:
                distinct_fields.append('sale_id')
        return distinct_fields


    
    def _action_cancel(self):
        ## tengo que cancelar tosdos los movimientos anteriores
        orig_ids_to_cancel= self.mapped('move_orig_ids')
        res = super()._action_cancel()
        if orig_ids_to_cancel:
            orig_ids_to_cancel.filtered(lambda x: not x.move_dest_ids)._action_cancel()
        return res
