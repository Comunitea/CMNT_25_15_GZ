# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011 Pexego Sistemas Informáticos. All Rights Reserved
#    $Javier Colmenero Fernández$
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, fields
from openerp import _, netsvc


class sale_order(orm.Model):
    _inherit = 'sale.order'

    def _picked_rate(self, cr, uid, ids, name, arg, context=None):
        """Sobrescribimos por completo el método, ya que en la query el order_id debe sacarse de las
        lineas y no del albarán"""
        if not ids:
            return {}
        res = {}
        tmp = {}
        for id in ids:
            tmp[id] = {'picked': 0.0, 'total': 0.0}
        cr.execute('''SELECT
                l.order_id as sale_order_id, sum(m.product_qty) as nbr,m.state as move_state,p.type as picking_type
            FROM
                stock_move m
            LEFT JOIN
                sale_order_line l on (l.id=m.sale_line_id)
            LEFT JOIN
                stock_picking p on (p.id=m.picking_id)
            WHERE
                l.order_id IN %s GROUP BY m.state, l.order_id, p.type''', (tuple(ids),) )

        for item in cr.dictfetchall():
            if item['move_state'] == 'cancel':
                continue
            #Comentado para no tener en cuenta las devoluciones al hacer el cálculo
            #~ if item['picking_type'] == 'in':#this is a returned picking
                #~ tmp[item['sale_order_id']]['total'] -= item['nbr'] or 0.0 # Deducting the return picking qty
                #~ if item['move_state'] == 'done':
                    #~ tmp[item['sale_order_id']]['picked'] -= item['nbr'] or 0.0
            if item['picking_type'] == 'out':
                tmp[item['sale_order_id']]['total'] += item['nbr'] or 0.0
                if item['move_state'] == 'done':
                    tmp[item['sale_order_id']]['picked'] += item['nbr'] or 0.0

        for order in self.browse(cr, uid, ids, context=context):
            if order.shipped:
                res[order.id] = 100.0
            else:
                res[order.id] = tmp[order.id]['total'] and (100.0 * tmp[order.id]['picked'] / tmp[order.id]['total']) or 0.0
        return res

    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        """ Sobrescribimos el método que calcula el % facturado del pedido de venta"""
        res = {}

        for sale in self.browse(cursor, user, ids, context=context):
            if sale.invoiced:
                res[sale.id] = 100.0
                continue
            tot = 0.0
            for invoice in sale.invoice_ids:
                if invoice.state not in ('draft', 'cancel'):
                    tot += invoice.amount_untaxed
            if tot:
                res[sale.id] = min(100.0, tot * 100.0 / (sale.amount_untaxed or 1.00))
            else:
                res[sale.id] = 0.0

        return res

    _columns = {
        'no_picking':fields.boolean('No picking'),
        'picked_rate': fields.function(_picked_rate, string='Picked', type='float'),
        'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced', type='float'),
    }
    _defaults = {
        'no_picking': True
    }

    def _prepare_order_picking(self, cr, uid, order, context=None):
        if order.no_picking:
            return {
                'name': "TO_DEL",
                'origin': order.name,
                'date': order.date_order,
                'type': 'out',
                'state': 'auto',
                'move_type': order.picking_policy,
                'sale_id': order.id,
                'address_id': order.partner_shipping_id.id,
                'note': order.note,
                'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
                'company_id': order.company_id.id,
            }
        else:
            return super(sale_order, self)._prepare_order_picking(cr, uid, order, context=context)

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """ Sobrescribimos el método que crea los movimientos a partir de las lineas y los albarana, para
        que una vez creado el albarán lo elimine y desasigne al albarán de los movimientos"""
        res = super(sale_order,self)._create_pickings_and_procurements(cr, uid, order, order.order_line, None, context=context)
        if order.no_picking:
            order = self.browse(cr, uid, order.id, context=context)
            for pick in order.picking_ids:
                del_ids = self.pool.get('stock.move').search(cr,uid,[('picking_id','=',pick.id)])
                self.pool.get('stock.move').write(cr,uid,del_ids,{'picking_id' : False})
                # Write the correct warehouse in each move
                for move in self.pool.get('stock.move').browse (cr, uid, del_ids):
                    warehouse_id = self.pool.get('stock.location')._get_warehouse(cr, uid, [move.location_id.id])
                    self.pool.get('stock.move').write(cr, uid, move.id, {'warehouse_id': warehouse_id})
                self.pool.get('stock.picking').unlink(cr,uid,[pick.id])
        return True

    def check_moves(self,cr,uid,ids):
        """ True si todos los movimientos asociados a las lineas de venta estan en done o cancel"""
        res = False
        for sale in self.browse(cr,uid,ids):
            for line in sale.order_line:
                for move in line.move_ids:
                    if move.picking_id and move.picking_id.type == 'in':  # que ignore los movimientos de entrada, para que el flujo acabe aunque los movs de devolución estén sin procesar
                        continue
                    if move.state not in ('done','cancel'):
                        return False
                    else:
                        res = True
        return res

    def action_cancel(self, cr, uid, ids, context=None):
        """ Sobrescribimos el método para que no se pueda cancelar una orden,
        si los movimientos asociados a las lineas no están cancelados"""
        if context==None:
            context={}
        move_ids = []
        for sale in self.browse(cr,uid,ids,context=context):
            for line in sale.order_line:
                for move in line.move_ids:
                    move_ids.append(move.id)
                    if move.state != 'cancel':
                        raise orm.except_orm(_('Could not cancel sales order !'),_('You must first cancel all moves attached to sale order lines of this sales order.'))
        res = super(sale_order,self).action_cancel(cr, uid, ids, context=context)
        proc_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")
        for mov in move_ids:
            proc_ids = proc_obj.search(cr, uid, [('move_id', '=', mov)])
            if proc_ids:
                for proc in proc_ids:
                    wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)
        return res


class stock_move(orm.Model):
    _inherit = 'stock.move'

    def _get_move_origin(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for move in self.browse(cr, uid, ids):
            if move.picking_id:
                res[move.id] = move.picking_id.origin
            elif move.sale_line_id:
                res[move.id] = move.sale_line_id.order_id.name
            elif move.purchase_line_id:
                res[move.id] = move.purchase_line_id.order_id.name
            else:
                res[move.id] = ""

        return res

    def _search_by_origin(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        ids = []
        purchase_ids = self.pool.get('purchase.order').search(cr, uid, [('name', args[0][1], args[0][2])])
        sale_ids = self.pool.get('sale.order').search(cr, uid, [('name', args[0][1], args[0][2])])
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('origin', args[0][1], args[0][2])])
        if purchase_ids:
            for purchase in self.pool.get('purchase.order').browse(cr, uid, purchase_ids):
                if purchase.order_line:
                    ids.extend(self.pool.get('stock.move').search(cr, uid, [('purchase_line_id', 'in', [x.id for x in purchase.order_line])]))
        if sale_ids:
            for sale in self.pool.get('sale.order').browse(cr, uid, sale_ids):
                if sale.order_line:
                    ids.extend(self.pool.get('stock.move').search(cr, uid, [('sale_line_id', 'in', [x.id for x in sale.order_line])]))
        if picking_ids:
            ids.extend(self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', picking_ids)]))

        return [('id', 'in', list(set(ids)))]


    _columns = {
        'partner_id': fields.related('address_id','partner_id',type='many2one', relation="res.partner", string="Partner", store=True, select=True),
        'origin_comp': fields.function(_get_move_origin, method=True, type="char", size=64, string="Origin", readonly=True, fnct_search=_search_by_origin),
        'warehouse_id': fields.many2one ('stock.warehouse', 'Warehosue', readonly=True,),
    }

    _order = 'date desc'


class stock_location(orm.Model):
    _inherit = 'stock.location'

    def _get_warehouse (self, cr, uid, ids,context=None):

        warehouse_pool = self.pool.get('stock.warehouse')
        warehouse_ids = warehouse_pool.search(cr,uid,[])
        for location in self.browse(cr,uid,ids,context=context):
            for warehouse in warehouse_pool.browse (cr,uid, warehouse_ids):
                if location.id == warehouse.lot_stock_id.id or location.id in self._get_sublocations(cr, uid, warehouse.lot_stock_id.id, context=context):

                    return warehouse.id
        return False


class stock_picking(orm.Model):
    _inherit = 'stock.picking'
    _order = 'date desc'


    def action_undo(self, cr, uid, ids, context=None):
        """ Undo picking.
        @return: True
        """

        move_pool = self.pool.get('stock.move')
        for picking in self.browse(cr, uid, ids, context=context):
            move_ids = [x.id for x in picking.move_lines]
            move_pool.write(cr, uid, move_ids, {'picking_id': False})
        res = self.unlink(cr, uid, ids)

        data_pool = self.pool.get('ir.model.data')
        action = {}
        try:
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'stock', 'action_out_picking_move')
        except ValueError:
            raise orm.except_orm(_('Error'), _('Object reference %s not found' %'action_out_picking_move' ))
        if action_model:
            action_pool = self.pool.get(action_model)
            action = action_pool.read(cr, uid, action_id, context=context)
        return action


    def action_move(self, cr, uid, ids,context=None):
        """Heredamos este método para que al validar los movimientos del albarán,se los recorra y
        saque el id de la orden de venta asociada a los movimientos a traves de las lineas de venta
        para mandar la señal que permite que el flujo de venta avance a done."""
        if context is None:
            context = {}
        order_ids = set()
        res = super(stock_picking,self).action_move(cr, uid, ids,context=context)
        for pick in self.browse(cr,uid,ids,context=context):
            for move in pick.move_lines:
                if move.sale_line_id:
                    order_ids.add(move.sale_line_id.order_id.id)

        wf_service = netsvc.LocalService("workflow")
        for sale_id in order_ids:
            wf_service.trg_validate(uid, 'sale.order', sale_id, 'moves_done', cr) #decimos a la orden de venta que avance a hecho
        return res

    def _invoice_line_hook(self, cursor, user, move_line, invoice_line_id):
        """ Heredamos este método, para que al crear las lineas de factura, cuando facturamos desde albarán
        rellenemos el campo invoice_ids del pedido de venta asociado. para que el método _invoiced_rate de sale.order
        se calcule correctamente"""
        res = super(stock_picking, self)._invoice_line_hook(cursor, user, move_line, invoice_line_id)
        sale_obj = self.pool.get('sale.order')
        invoice_line_obj = self.pool.get('account.invoice.line')
        if move_line.sale_line_id:
            invoice_line = invoice_line_obj.browse(cursor,user,invoice_line_id)
            sale_obj.write(cursor, user, [move_line.sale_line_id.order_id.id],
                                    {
                                         'invoice_ids': [(4, invoice_line.invoice_id.id)],
                                    })
        return res

    def _get_account_analytic_invoice(self, cursor, user, picking, move_line):
        if (not picking.sale_id) and move_line.sale_line_id:
            return move_line.sale_line_id.order_id.project_id.id
        return super(stock_picking, self)._get_account_analytic_invoice(cursor, user, picking, move_line)

