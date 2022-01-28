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


    @api.multi
    def get_needed_qty(self, product, product_qty, product_uom):
        self.ensure_one()
        src_location_id = self.location_id.id
        product_location = product.with_context(location=src_location_id)
        virtual_available = product_location.virtual_available
        qty_available = product.uom_id._compute_quantity(virtual_available, product_uom)
        if qty_available > 0:
            if qty_available >= product_qty:
                return 0.0
            else:
                return product_qty - qty_available
        return product_qty


    def _action_confirm(self, merge=True, merge_into=False):
        moves = super()._action_confirm(merge=merge, merge_into=merge_into)
        ## Filtro todos los componenetes de producciones que NO está asignados y son make_to_stock
        import pdb; pdb.set_trace()
        for move in self.filtered(lambda x: x.raw_material_production_id and x.state in ['confirmed', 'partially_available'] and x.procure_method =='make_to_stock'):
            needed_qty = move.get_needed_qty(move.product_id, move.product_uom_qty, move.product_uom)
            if needed_qty > 0:
                ## Busco un fabricar o comprar
                ## Miro si el producto es fabricar o comprar y busco una regla
                product_id = move.product_id
                product_rule_id = product_id.route_ids.mapped('pull_ids').filtered(lambda x: x.action in ['buy', 'manufacture'])
                if product_rule_id[0].action == 'buy':
                    action = 'buy'
                else:
                    action = 'manufacture'
                group_id = move.group_id
                ## Busco una regla para ese almacén, ese ubicación y esa acción
                values = move._prepare_procurement_values()
                route_id = move.raw_material_production_id.move_finished_ids.move_dest_ids.rule_id.route_id
                if group_id and route_id:
                    domain = [('action', '=', action), ('route_id', '=', route_id.id)]
                    ctx = self._context.copy()
                    ctx.update(rule_domain=domain)
                    rule_id = group_id.with_context(ctx)._get_rule(product_id, move.location_id, values)
                    if rule_id:
                        origin = '{} -> {}'.format(move.group_id.name, move.raw_material_production_id.name)
                        getattr(rule_id, '_run_%s' % rule_id.action)(move.product_id, needed_qty, move.product_uom, move.location_id, move.rule_id and move.rule_id.name or "/", origin, values)       
        return moves

    