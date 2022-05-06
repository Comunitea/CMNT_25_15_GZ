# -*- coding: utf-8 -*-
# Copyright 2018 Kiko Sánchez, <kiko@comunitea.com> Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)
DOMAIN_NOT_STATE = ['draft', 'cancel']

class StockMove(models.Model):

    _inherit = "stock.move"

    sale_id = fields.Many2one('sale.order', 'Saler Order')
    prev_move_orig_ids = fields.Many2many(
        'stock.move', 'prev_stock_move_move_rel', 'move_dest_id', 'move_orig_id', 'Prev Original Move',
        copy=False,
        help="Optional: previous stock move when chaining them sored to retrieve")
    locked_workflow = fields.Boolean('Move Workflow Locked')

    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals['sale_id'] = self.sale_id.id
        return vals
    
    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        sale_id = self.sale_id and self.sale_id.id
        if sale_id:
            # vals['sale_id'] = sale_id
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
        orig_ids_to_cancel= self.mapped('move_orig_ids').filtered(lambda x: x.state != 'done')
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
        ## NO SE PORQUE PERO A VECES ENTRA VACIO Y FALLA EN EL BUCLE
        if not self:
            return moves
        ## Filtro todos los componenetes de producciones que NO está asignados y son make_to_stock
        if self:
            moves.raw_ids_action_assign()
        return moves
    
    def raw_ids_action_assign(self):
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
        return True
    
    @api.multi
    def change_to_mto(self):
        if len(self) == 1:
            self._change_to_mto()
            return self._action_open_stock_move_workflow()

        res = False
        for move in self:
            res = move._change_to_mto()
        return res

    
    def _change_to_mto(self):
        if self.prev_move_orig_ids:
            self.move_orig_ids = self.prev_move_orig_ids
        _logger.info("Cambiado el aprovisionamiento del moviento {}: {} a 'Generar orden'".format(self.id, self.display_name))
        self.procure_method='make_to_order'
        self.state='confirmed'
        #self._action_assign()

    @api.multi
    def change_to_mts(self):
        if len(self) == 1:
            self._change_to_mts()
            return self._action_open_stock_move_workflow()
        for move in self:
            res = move._change_to_mts()
    
    def _change_to_mts(self):

        if self.move_orig_ids:
            self.prev_move_orig_ids = self.move_orig_ids
            self.move_orig_ids = self.env['stock.move']    
        self.procure_method='make_to_stock'
        self.state = 'confirmed'
        
    @api.multi
    def do_unreserve(self):
        if len(self) == 1:
            self._do_unreserve()
            return self._action_open_stock_move_workflow()

        for move in self:
            move._do_unreserve()


    @api.multi
    def do_action_assign(self):
        if len(self) == 1:
            self._action_assign()
            return self._action_open_stock_move_workflow()
        for move in self:
            move._action_assign()

    @api.multi
    def generate_procurement_order(self):
        for move in self.filtered(lambda x: x.state in ['confirmed', 'partially_available', 'waiting']):
            _logger.info("Se genera aprovisionamiento para el mov. {}: {}".format(move.id, move.display_name))
            if move.procure_method == 'make_to_stock':
                move._action_assign()
            else:
                move._generate_procurement_order()
        if len(self) == 1:
            return self._action_open_stock_move_workflow()


    def _propagate_extended_date(self):
        for move in self:
            if move.move_dest_ids:
                for move_dest_id in move.move_dest_ids:
                    expected_date = min(move.expected_date, move_dest_id.expected_date)

    def _generate_procurement_order(self):
        ## Esta función lanza una regla de aprovisionamiento para abastecer
        ## Se puede usar cuanto este en parcialmente disponible o asignado, 
        ## Genera una compra/fabricación PERO NO los deja enlazados.
        if self.procure_method == 'make_to_order' and self.state in ['confirmed', 'partially_available']:
            _logger.info("Se genera aprovisionamiento para el mov. {}: {}".format(self.id, self.display_name))
            rule = self.env['procurement.rule']
            needed_qty = self.product_uom_qty - self.reserved_availability 
            product_id = self.product_id
            picking_type_id = self.picking_type_id or self.raw_material_production_id.picking_type_id
            wh_id = picking_type_id.warehouse_id
            origin = self.group_id.name
            values=self._prepare_procurement_values()
            _logger.info("%s -> %s "%(fields.Datetime.now(),values['date_planned']))
            date = max(fields.Datetime.now(), values['date_planned'])
            date_planned = datetime.strptime(date, DEFAULT_SERVER_DATETIME_FORMAT) ### + timedelta(days=3)
            values['date_planned'] = date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            mto_rule_id = product_id.get_default_mto_rule_id(self.location_id, values)
            if not mto_rule_id:
                raise ValidationError("El artículo %s no tiene una regla de aprovisionamiento"%product_id.display_name)
            ### Compruebo si ya hay una compra asociada a este movimiento
            if mto_rule_id.action =='buy':
                domain = [('move_dest_ids', '=', self.id), ('order_id.origin', 'ilike', origin)]
                pol = self.env['purchase.order.line'].search(domain)
                if pol:
                    raise ValidationError("Ya hay una compra asociada %s"%pol.order_id.name)
            if mto_rule_id.action =='manufacture':
                domain = [('move_dest_ids', '=', self.id)]
                pol = self.env['purchase.order.line'].search(domain)
                if pol:
                    raise ValidationError("Ya hay una compra asociada %s"%pol.order_id.name)
            if needed_qty >= 0.0:
                getattr(mto_rule_id, '_run_%s' % mto_rule_id.action)(
                    product_id, needed_qty, self.product_uom, self.location_id, self.name,
                    origin, values)
                ##if mto_rule_id.action =='buy':
                self.state = 'waiting'
            return True
        return False


    def action_toggle_workflow_locked(self):
        self.locked_workflow = not self.locked_workflow
        return self._action_open_stock_move_workflow()

    @api.multi
    def action_open_stock_move_workflow(self):
        self.ensure_one()
        ## Siempre en modo lectura ???????
        self.locked_workflow = True
        ## obj = self.picking_id or self.raw_material_production_id or self.production_id
        ## obj.is_locked = True
        return self._action_open_stock_move_workflow()
    
    @api.multi
    def _action_open_stock_move_workflow(self):
        action = self.env.ref('stock.stock_move_action').read()[0]
        form_view = self.env.ref("procurement_group_extended.view_stock_move_workflow").id
        action.update({
            "target": 'new', 
            "view_mode": "form",
            "views": [(form_view, "form")],
            "res_id": self.id,
            ##'flags': {'initial_mode': 'view'}
        })
        
        return action