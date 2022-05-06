##############################################################################
#
#    Copyright (C) 2020-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Kiko Sánchez$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, exceptions, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero, float_compare

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):

    _inherit = "stock.move"

    @api.multi
    def _get_move_dest_info(self):
        for move in self:
            text = ''
            if move.move_dest_ids:
                total_qty = sum((x.product_uom_qty - x.reserved_availability) for x in move.move_dest_ids)
                location_id = move.move_dest_ids.mapped('location_id')
                text = "%d %s para %s (%d)"%(total_qty, move.product_uom.edi_code, location_id.name, len(move.move_dest_ids))
            move.move_dest_info = text

    procurement_route_id = fields.Many2one(related="rule_id.route_id")
    move_dest_info = fields.Char("Move Dest Info", compute="_get_move_dest_info")

    
    def _get_new_picking_domain(self):
        domain = super()._get_new_picking_domain()
        if self.picking_type_id.code == 'outgoing':
            domain += [('partner_id', '=', self.partner_id.id)]
            if self.sale_id:
                domain += [('sale_id', '=', self.sale_id.id)]
        return domain
    
    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        if self.rule_id:
            vals['rule_id'] = self.rule_id.id
        return vals

    def _prepare_move_split_vals(self, qty):
        vals = super()._prepare_move_split_vals(qty)
        if self._context.get('location_dest_id', False):
            vals.update(location_dest_id= self._context.get('location_dest_id'))
        if self._context.get('picking_type_id', False):
            vals.update(picking_type_id=self._context.get('picking_type_id'))
        if self._context.get('procure_method', False):
            vals.update(procure_method=self._context.get('procure_method'))
        if self._context.get('rule_id', False):
            vals.update(rule_id=self._context.get('rule_id'))
        return vals

    def _action_assign(self):
        return super()._action_assign()

    """
    def check_split_excess_qty_move(self):
        ##Si reune las condiciones, generará un nuevo movimiento con la cantidad que no tenga destino
        ## La idea es coger la mercancía que haya y "Ubicarla"
        STATES = ['waiting', 'assigned', 'partially_available', 'confirmed']
        for move in self.filtered(lambda x:
            x.product_id.type == 'product' and 
            x.picking_type_id.excess_picking_type_id and 
            x.move_dest_ids):
            
            precision = move.product_uom.rounding
            ## Todos los movimientos que llegan a los mov de destino que no estén hechos
            move_dest_ids = move.move_dest_ids.filtered(lambda x: x.state in STATES)
            ## CAntidad que necesito: Cantidad en product_uom_qty en moves destino
            need_qty = sum(x.product_uom_qty for x in  move.move_dest_ids) 
            ## No se porque en el move origids tengo que quitar asi
            move_orig_ids = move.move_dest_ids.mapped('move_orig_ids')
            ## cantidad a abastecer los move_dest_ids
            supplied_qty = sum(x.product_uom_qty for x in move_orig_ids)
            qty_to_split = supplied_qty - need_qty
            
            if float_compare(qty_to_split, 0, precision_rounding=precision) > 0:
                type_id = move.picking_type_id.excess_picking_type_id
                copy_vals = {
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': type_id.default_location_dest_id.id,
                    'picking_type_id': type_id.id,
                    'product_uom_qty': qty_to_split,
                    'picking_id': False,
                    'rule_id': False,
                    'procure_method': 'make_to_stock'}
                stock_move = move.copy(copy_vals)
                stock_move._action_confirm()
                stock_move._action_assign()
                stock_move._assign_picking()
        return True


    def _push_apply(self):
        Push = self.env['stock.location.path']
        ##  Hacemos un push apply para las cantidades que faltam
        res = super()._push_apply()
        ctx = self._context.copy()
        for move in self.filtered(lambda x: x.state == 'done' and x.move_dest_ids):
            dest_qties = sum((x.product_uom_qty - x.quantity_done) for x in move.move_dest_ids)
            free_qty = move.quantity_done > dest_qties
            if free_qty > 0:
                
                # if the move is a returned move, we don't want to check push rules, as returning a returned move is the only decent way
                # to receive goods without triggering the push rules again (which would duplicate chained operations)
                domain = [('location_from_id', '=', move.location_dest_id.id)]
                # priority goes to the route defined on the product and product category
                routes = move.product_id.route_ids | move.product_id.categ_id.total_route_ids
                rules = Push.search(domain + [('route_id', 'in', routes.ids)], order='route_sequence, sequence', limit=1)
                if not rules:
                    # TDE FIXME/ should those really be in a if / elif ??
                    # then we search on the warehouse if a rule can apply
                    if move.warehouse_id:
                        rules = Push.search(domain + [('route_id', 'in', move.warehouse_id.route_ids.ids)], order='route_sequence, sequence', limit=1)
                    elif move.picking_id.picking_type_id.warehouse_id:
                        rules = Push.search(domain + [('route_id', 'in', move.picking_id.picking_type_id.warehouse_id.route_ids.ids)], order='route_sequence, sequence', limit=1)
                # Make sure it is not returning the return
                if rules and (not move.origin_returned_move_id or move.origin_returned_move_id.location_dest_id.id != rules.location_dest_id.id):
                    ctx.update (default_product_uom_qty=free_qty)
                    rules.with_context(ctx)._apply(move)
        return res
    """
    def change_incoming_moves_to_storage(self):
        for move in self:
            if move.filtered(lambda x:x.picking_code != 'incoming'):
                raise ValidationError (_("Only 'incoming' picking types"))
            if move.state in ['done', 'cancel']:
                raise ValidationError (_("Move in incorrect state"))
            if any(x.state in ['done', 'cancel'] for x in move.move_dest_ids):
                raise ValidationError (_("Move in incorrect state"))
            move.move_dest_ids = self.env['stock.move']
            move.move_dest_ids.write({'procure_method': 'make_to_stock'})
            
    """
    def change_incoming_moves_to_storage_bis(self):
    
        """ 
    """
        EN RECEPCIONES : LOCATION_DEST_ID = entradas

        esta función quita el enlace entre entradas y salidas, y deja el de salida a stock.
        Entrada en stock: El movimiento de entrada a salida se duplica y se cambia destino por stock. Se busca un tipo de albarán adecuado
        Salida de stock: El movimiento de entrada a salida se duplica y se cambia origen por stock. Sigue siendo el mismo tipo de albarán

        Proveedores   >>>>    Entrada             >>>>            Salida  >>>>    Clientes

        Proveedores   >>>>    Entrada     >>>>    Stock   >>>>    Salida  >>>>    Clientes
        """
    """


        self.ensure_one()
        # Solo recepciones.
        if self.filtered(lambda x:x.picking_code != 'incoming'):
            raise ValidationError (_("Only 'incoming' picking types"))


        warehouse_id = self.picking_type_id.warehouse_id
        Entrada = warehouse_id.wh_input_stock_loc_id ## self.env.ref('stock.stock_location_company')
        Salida = warehouse_id.wh_output_stock_loc_id ## self.env.ref('stock.stock_location_output')
        Stock = warehouse_id.lot_stock_id ## self.env.ref('stock.stock_location_stock')
        
        for move in self:
            if move.location_dest_id != Entrada:
                continue
            move_Entrada_Salida = move.move_dest_ids.filtered(lambda x: x.location_dest_id == Salida)
            if not move_Entrada_Salida:
                continue
            OutgoingMove = move_Entrada_Salida.move_dest_ids
            IncomingMove = move

            # Creo el movimiento de entrada a stock
            domain_picking_type = [('default_location_src_id', '=', Entrada.id), ('default_location_dest_id', '=', Stock.id)]
            ubi_type_id = self.picking_type_id.search(domain_picking_type, limit=1)
            if not ubi_type_id:
                raise ValidationError (_('Ubication type not found'))
            copy_vals = {'picking_id': False,
                         'picking_type_id': ubi_type_id.id,
                         'location_dest_id': Stock.id}
            if IncomingMove:
                copy_vals['move_orig_ids'] = [(6, 0, [IncomingMove.id])]
            move_Entrada_Stock = move_Entrada_Salida.copy(copy_vals)

            # Creo el movimiento de stock a salida
            copy_vals = {'picking_id': False,
                         'location_id': Stock.id,
                         'procure_method': 'make_to_stock'}
            if OutgoingMove:
                copy_vals['move_dest_ids'] = [(6, 0, OutgoingMove.ids)]
            move_Stock_Salida = move_Entrada_Salida.copy(copy_vals)

            #Quito enlaces para no propagar cancelación.
            move_Entrada_Salida.write({'move_dest_ids': [(5)],
                                       'move_orig_ids': [(5)]})
            move_Entrada_Salida._action_cancel()



            move_Stock_Salida._action_confirm()
            move_Stock_Salida._action_assign()
            move_Entrada_Stock._action_confirm()
            move_Entrada_Stock._action_assign()
            ctx = self._context.copy()
            ctx.update(assign_picking_domain=[('location_id', '=', Entrada.id), ('location_dest_id', '=', Stock.id)])
            move_Entrada_Stock.with_context(ctx)._assign_picking()
            ctx.update(assign_picking_domain=[('location_id', '=', Stock.id), ('location_dest_id', '=', Salida.id)])
            move_Stock_Salida._assign_picking()

    """

    def change_moves_to_stockage(self):
        """ EN SALIDAS : LOCATION_DEST_ID.USAGE = CUSTOMER
        Esta función cambia un movimiento de salida que ha sido creado con regla make_to_stock a make_to_order

        Picking     >>>>    Salida  >>>>    Clientes
        (make_to_order - waiting)
        Picking     >>>>    Salida  >>>>    Clientes
        (make_to_stock - en espera/reservado)
        """
        location_dest_id = self.mapped('location_dest_id')
        if len(location_dest_id) != 1:
            raise ValidationError (_('Todos los albaranes deben de ir a la misma ubicación'))
        # Como supongo que los movimientos son de salida, la ubicación de destino debería ser salidas.
        if location_dest_id.usage != 'customer':
            raise ValidationError (_('Only outgoing pickings'))
        
        warehouse_id = self.picking_type_id.warehouse_id

        ## Entrada = warehouse_id.wh_input_stock_loc_id ## self.env.ref('stock.stock_location_company')
        ## Salida = warehouse_id.wh_output_stock_loc_id ## self.env.ref('stock.stock_location_output')
        ## Stock = warehouse_id.lot_stock_id ## self.env.ref('stock.stock_location_stock')
        group_id = self.group_id
        for move in self:
            if not move.sale_line_id:
                raise ValidationError (_('Only if sale line in move'))
                continue
            orig_move_ids = move.move_orig_ids
            
            if any(x.state == 'done' for x in orig_move_ids):
                raise ValidationError (_('You have any pre-move done'))
            ## Además, solo permito si los moviemitnos anteriores son del mismo grupo de abastecimietno.
            ## en estado distinto a draft, cancel, done
            orig_move_ids = move.move_orig_ids            
            if orig_move_ids:
                if any(x.group_id != group_id for x in orig_move_ids):
                    raise ValidationError(_('Move %s have different group than one move orig'))
                ## Puede tener varios movimeintos previos, pero TODOS deben ir al este
                if len(orig_move_ids) > 1 and orig_move_ids.mapped("move_dest_ids") != move:
                    raise ValidationError(_('Move %s have more than one move orig'))
                if len(orig_move_ids.mapped('move_dest_ids')) > 1:
                    raise ValidationError(_('Orig moves for Move %s have more than one move dest'))
                #orig_move_ids._do_unreserve()
                #if orig_move_ids.procure_method == 'make_to_order':
                orig_move_ids._action_cancel()
            ## Cancelo el movieminto. Esto cancela los anteriores, si cumplen condiciones anteriores.
            move._action_cancel()
        ## Busco la regla contra stock de
        route = self.mapped('procurement_route_id')
        
        ctx = self._context.copy()
        ctx.update(new_picking=True)
        line_ids = self.env['sale.order.line']
        ##vuelvo a lanzar el procurement de la línea de venta, pero con distinta acción
        for sale_line_id in self.mapped('sale_line_id'):
            rule_domain = [('action', '=', 'move')]
            if sale_line_id.route_id:
                rule_domain=[('action', '=', 'move'), ('route_id', 'in', route.ids)]
            ctx.update(rule_domain=rule_domain)
            sale_line_id.state = 'sale'
            sale_line_id.with_context(ctx)._action_launch_procurement_rule()
            line_ids |= sale_line_id

        new_move_ids = line_ids.mapped('move_ids')
        new_move_ids |= new_move_ids.mapped('move_orig_ids')
        new_move_ids = new_move_ids.filtered(lambda x: x.state not in ['cancel', 'done'])
        sp_ids = new_move_ids.mapped('picking_id')
        new_move_ids._action_assign()
        if sp_ids:
            for sp in sp_ids:
                post = 'This picking was created changing procurement from storage location.'
                sp.message_post(post)


    def reassing_split_from_picking(self):
        ## Crea nuevos albaranes si se cambian las fechas de los movimientos.

        picking_id = self.mapped('picking_id')
        if picking_id.state in ['cancel', 'draft', 'done']:
            raise ValidationError('El albarań %s está en estado incorrecto: %s'%(picking_id.name, picking_id.state))
        if len(picking_id) != 1:
            raise ValidationError('Todos los movimientos deben ser del mismo albarán')
        if any(x.picking_id == False for x in self):
            raise ValidationError('Todos los movimientos deben tener ya un albarán asignado')
        scheduled_date = picking_id.scheduled_date
        moves_to_split = self.filtered(lambda x: x.date_expected != scheduled_date)
        moves_to_split.write({'picking_id': False})
        backorder_ids = self.env['stock.picking']
        dates = {}
        for move in moves_to_split:
            if not move.date_expected in dates.keys():
                dates[move.date_expected] = move.date_expected

        if dates:
            for date in dates.keys():
                dates[date] = moves_to_split.filtered(lambda x: x.date_expected == date)
                if picking_id.scheduled_date == date:
                    dates[date].write({'picking_id': picking_id})
                else:
                    backorder_picking = picking_id.copy({
                        'name': '/',
                        'move_lines': [],
                        'move_line_ids': [],
                        'backorder_id': picking_id.id,
                    })
                    picking_id.message_post(
                        body=_(
                            'Este albarán ha creado un nuevo albarán <a href="#" '
                            'data-oe-model="stock.picking" '
                            'data-oe-id="%d">%s</a> al cambiar la fecha de estimada a %s.'
                        ) % (
                                 backorder_picking.id,
                                 backorder_picking.name,
                                 date
                             )
                    )
                    dates[date].write({
                        'picking_id': backorder_picking.id,
                    })
                    dates[date].mapped('move_line_ids').write({
                        'picking_id': backorder_picking.id,
                    })
                    backorder_ids |= backorder_picking
            if backorder_ids:
                action = self.env.ref('stock.action_picking_tree_all').read()[0]
                action['domain'] = [('id', 'in', backorder_ids.ids)]
                return action
        return


    @api.multi
    def apply_change_procurement(self):
        for move in self:
            if move.picking_type_id.code == 'outgoing' and move.procure_method == 'make_to_order':
                move.change_moves_to_stockage()
            else:
                raise ValidationError ('No hay operación disponible para este movimiento')
        return True
