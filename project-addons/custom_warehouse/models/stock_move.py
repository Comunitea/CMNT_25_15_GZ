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

    procurement_route_id = fields.Many2one(related="rule_id.route_id")
    overprocess_by_supplier = fields.Boolean('Overprocess by supplier min qty. Exceed must go to stock', default=False)

    def _get_new_picking_domain(self):
        domain = super()._get_new_picking_domain()
        if self.picking_type_id.code == 'outgoing':
            domain += [('partner_id', '=', self.partner_id.id)]
            if self.sale_id:
                domain += [('sale_id', '=', self.sale_id.id)]
        return domain
    """
    def _assign_picking(self):
        ctx = self._context.copy()
        ctx.update(assign_picking_domain=self.get_domain_for_assign_picking())
        return super(StockMove, self.with_context(ctx))._assign_picking()
    """
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

    def split_excess_to_stock(self, qty_done=True):
        return True
        ## si recibimos má cantidad que la que necesitamos, entonces se envían a stock

        ## Si qty_done = True hacemos split sobre la cantidad hecha,
        # si no sobre la cantidad que se necesita en los siguientes movimientos
        ctx = self._context.copy()
        res = self.env['stock.move']

        for move in self:
            
            _logger.info('%s: desde %s a %s. %s'%(move.display_name, move.location_id.name, move.location_dest_id.name, move.product_uom_qty))
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            need_qty = sum(x.product_uom_qty for x in move.move_dest_ids)
            
            if not qty_done:
                to_stock_qty = move.product_uom_qty - need_qty
            else:
                to_stock_qty = move.product_uom_qty - move.quantity_done

            location_dest_id = move.warehouse_id.lot_stock_id
            if float_is_zero(to_stock_qty, precision_digits=precision):
                continue
            ## si el movimiento siguiente tienen menos cantidad, el resto va para stock
            _logger.info("Split move in {} to {} and {} to {}".format(need_qty, move.location_dest_id.name, to_stock_qty, location_dest_id.name))
            # cojo el primero
            next_move = move.move_dest_ids[0]
            # La ruta seleccionada es
            rule_id = next_move.rule_id
            if not rule_id:
                raise ValidationError(_('Not rule for excess purchases'))
            #next_move.product_uom_qty += to_stock_qty
            #next_move._do_unreserve()

            _logger.info("El movimiento original a salida se queda con  {}".format(next_move.product_uom_qty))

            rule_domain = [
                          ('location_src_id', '=', next_move.location_id.id),
                          ('location_id', '!=', next_move.location_dest_id.id),
                          ('action', '=', 'move'),
                          ('route_id', '=', rule_id.route_id.id),
                          ('procure_method', '=', 'make_to_stock')]
            rule_id = move.rule_id.search(rule_domain, limit=1)
            if not rule_id:
                raise ValidationError(_('Not rule for movs from {} to {}'.format(next_move.location_id.name, location_dest_id.name)))
            _logger.info("Encuentro la regla  {}".format(rule_id.display_name))
            ctx.update({
                'location_dest_id': rule_id.location_id,
                'procure_method': rule_id.procure_method,
                'picking_type_id': rule_id.picking_type_id.id,
                'rule_id': rule_id.id,
            })
            new_move = next_move.browse(next_move.with_context(ctx)._split(to_stock_qty))
            new_move.picking_id = False
            if not ctx.get('no_assign_picking', False):
                new_move._assign_picking()
            move.move_dest_ids |= new_move
            new_move.move_dest_ids = False
            _logger.info(
                "El movimienro nuevo a stock se queda con  {} y picking {}".format(new_move.product_uom_qty,
                                                                                    new_move.picking_id.name))
            res |= new_move

        return res

    def _action_assign(self):
        return super()._action_assign()
        m_ids = self.filtered(lambda x: x.overprocess_by_supplier and x.state in ('confirmed', 'waiting', 'assigned'))
        if m_ids:
            m_ids.split_excess_to_stock()
        return super()._action_assign()

    def _action_done(self):
        excess_moves = self.filtered(lambda x: x.picking_type_id.excess_location_id)
        if excess_moves:
            excess_moves.check_split_move()
        res =  super()._action_done()
        return res

    def check_split_move(self):
        ##todo Revisar
        STATES = ['waiting', 'assigned', 'partially_available']
        for move in self.filtered(lambda x:x.move_dest_ids):
            precision = move.product_uom.rounding
            ## Todos los movimientos que llegan a los mov de destino que no estén hechos
            move_dest_ids = move.move_dest_ids.filtered(lambda x: x.state in STATES)

            ## No se porque en el move origids tengo que quitar asi
            move_orig_ids = move.mapped('move_dest_ids.move_orig_ids') - move - move_dest_ids

            move_orig_ids_not_done = move_orig_ids.filtered(lambda x: x.state in STATES)
            if move_orig_ids_not_done:
                """ En este caso hay varios albarnes que podrían alimentar el de destino, por lo que no puedo saber cuanto hay que ubicar"""
                _logger.info("No se puede definir la cantidad sobrante, porque hay otros movimientos pendientes")
                continue
            
            

            ## supongo que el resto de movimientos que suministran el de destino están hechos, por lo que la reserva irá aumentantdo
            need_qty =sum(x.product_uom_qty - x.reserved_availability for x in move_dest_ids)
            
            if float_compare(move.quantity_done, need_qty, precision_rounding=precision) > 0:
                excess_qty = move.quantity_done - need_qty
                type_domain = [('warehouse_id', '=', move.picking_type_id.warehouse_id.id),
                               ('default_location_src_id', '=', move.location_dest_id.id),
                               ('default_location_dest_id', '=', move.picking_type_id.excess_location_id.id)]
                type_id = self.env['stock.picking.type'].search(type_domain)
                if not type_id:
                    _logger.info("No se ha encontrado un tipo de albarán para overprocess")
                copy_vals = {
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': type_id.default_location_dest_id.id,
                    'picking_type_id': type_id.id,
                    'product_uom_qty': excess_qty,
                    #'move_orig_ids': [(6, 0, [move.id])],
                    'picking_id': False,
                    'rule_id': False,
                    'procure_method': 'make_to_stock'}
                stock_move = move.copy(copy_vals)
                stock_move._action_confirm()
                stock_move._action_assign()
                stock_move._assign_picking()
                ## Tengo que quitar los predecesores, ya que no es capaz de reservar correctamente
                
                    #_logger.info(_('Move %s (%s) for %s %s overprocessed in %s') %
                    #             (stock_move.name, stock_move.picking_id.name, need_qty, stock_move.product_uom_name, self.picking_id.name))
        return True

    def _push_apply(self):
        ##todo Revisar
        return super()._push_apply()
        # Si llega una cantidad a entrada, tiene moviemiento de destino y la cantidad que llega es mayor que
        # la del movieminto de destino, lo que sobre debe de ir a stock.
        if self.move_dest_ids and self.location_dest_id == self.env.ref('stock.stock_location_company'):
            product_uom_qty = self.product_uom_qty - sum(x.product_uom_qty for x in self.move_dest_ids)
            if product_uom_qty:
                location_dest_id = self.env.ref('stock.stock_location_stock').id
                picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'internal'), ('default_location_dest_id', '=', location_dest_id)], limit=1)
                move_to_stock = self.copy()
                vals = {'location_id': self.location_dest_id.id,
                        'location_dest_id': location_dest_id,
                        'product_uom_qty': product_uom_qty,
                        'picking_type_id': picking_type_id.id,
                        'picking_id': False,
                        'move_orig_ids': [(4, self.id)]}
                move_to_stock.write(vals)
                move_to_stock._action_assign()
                move_to_stock._action_confirm()
                move_to_stock.move_orig_ids = self
        return super()._push_apply()

    """
    @api.model
    def _search_rule(self, product_id, values, domain):
        if self._context.get('rule_domain', False):
            domain = self._context['rule_domain'] + domain
        return super()._search_rule(product_id=product_id, values=values, domain=domain)
    """
    def change_incoming_moves_to_storage(self):

        """ EN RECEPCIONES : LOCATION_DEST_ID = entradas

        esta función quita el enlace entre entradas y salidas, y deja el de salida a stock.
        Entrada en stock: El movimiento de entrada a salida se duplica y se cambia destino por stock. Se busca un tipo de albarán adecuado
        Salida de stock: El movimiento de entrada a salida se duplica y se cambia origen por stock. Sigue siendo el mismo tipo de albarán

        Proveedores   >>>>    Entrada             >>>>            Salida  >>>>    Clientes

        Proveedores   >>>>    Entrada     >>>>    Stock   >>>>    Salida  >>>>    Clientes
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

        Entrada = warehouse_id.wh_input_stock_loc_id ## self.env.ref('stock.stock_location_company')
        Salida = warehouse_id.wh_output_stock_loc_id ## self.env.ref('stock.stock_location_output')
        Stock = warehouse_id.lot_stock_id ## self.env.ref('stock.stock_location_stock')

        sol_dict = {}
        moves = self.env['stock.move']
        for move in self:
            if not move.sale_line_id:
                continue

            sol_dict[move.sale_line_id] = move.product_uom_qty
            ## Además, solo permito si los moviemitnos anteriores son del mismo grupo de abastecimietno.
            ## en estado distinto a draft, cancel, done
            orig_move_ids = move.move_orig_ids.filtered(
                lambda x: x.group_id == move.group_id 
                and x.state not in ['draft', 'cancel', 'done'])
            # move._action_cancel()
            # move._do_unreserve()
            moves |= move

            if orig_move_ids:
                ## Puede tener varios movimeintos previos, pero TODOS deben ir al este
                if len(orig_move_ids) > 1 and orig_move_ids.mapped("move_dest_ids") != move:
                    raise ValidationError(_('Move %s have more than one move orig'))
                if len(orig_move_ids.mapped('move_dest_ids')) > 1:
                    raise ValidationError(_('Orig moves for Move %s have more than one move dest'))

                #orig_move_ids._do_unreserve()
                #if orig_move_ids.procure_method == 'make_to_order':
                moves |= orig_move_ids
        ## Cancelo el movieminto. Esto cancela los anteriores, si cumplen condiciones anteriores.
        moves._action_cancel()
        ctx = self._context.copy()
        ctx.update(new_picking=True,
                   rule_domain=[('action', '=', 'move')])
        line_ids = self.env['sale.order.line']
        ##vuelvo a lanzar el procurement de la línea de venta, pero con distinta acción
        for sale_line_id in sol_dict.keys():
            sale_line_id.state = 'sale'
            sale_line_id.with_context(ctx)._action_launch_procurement_rule()
            line_ids |= sale_line_id

        new_move_ids = line_ids.mapped('move_ids').filtered(
            lambda x: x.location_dest_id.usage == 'customer' and x.state != 'cancel')
        new_move_ids |= new_move_ids.mapped('move_orig_ids').filtered(lambda x: x.location_id.usage == 'internal' and x.state != 'cancel')
        sp_ids = new_move_ids.mapped('picking_id')
        new_move_ids._action_assign()
        if sp_ids:
            for sp in sp_ids:
                post = 'This picking was created changing procurement from storage location.'
                sp.message_post(post)


    def reassing_split_from_picking(self):
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
            
            elif move.picking_type_id.code == 'incoming':
                move.change_moves_to_stockage() 
            else:
                raise ValidationError ('No hay operación disponible para este movimiento')


        return True
