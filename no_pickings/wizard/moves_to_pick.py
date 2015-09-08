# -*- coding: utf-8 -*-
from openerp.osv import orm, fields
import openerp.addons.decimal_precision as dp
from datetime import datetime
from openerp import _, netsvc


class moves_to_pick_line(orm.TranientModel):
    _name = "moves.to.pick.line"
    _inherit = "stock.partial.picking.line"
    _columns = {
        'wizard_id': fields.many2one('moves.to.pick',string="Wizard", ondelete='CASCADE'),
    }


class moves_to_pick(orm.TransientModel):
    _name = "moves.to.pick"
    _columns = {
        'move_ids' : fields.one2many('moves.to.pick.line', 'wizard_id', 'Product Moves')
    }

    def _partial_move_for(self, cr, uid, move):
        """Devuelve el diccionario, para crear los move.to.pick.lines, con los valores
        del movimiento original"""
        partial_move = {
            'product_id' : move.product_id.id,
            'quantity' : move.product_qty or 0,
            'product_uom' : move.product_uom.id,
            'prodlot_id' : move.prodlot_id.id,
            'move_id' : move.id,
            'location_id' : move.location_id.id,
            'location_dest_id' : move.location_dest_id.id,
        }
        if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
            partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
        return partial_move

    def default_get(self, cr, uid, fields, context=None):
        """ Pasa los movimientos al asistente comprobando que las direcciones de destino  y los almacenes de origen son
        iguales"""
        if context is None: context = {}
        res = {}
        id_address = False
        id_warehouse = False
        move_ids = context.get('active_ids', [])

        if not move_ids or not context.get('active_model') == 'stock.move':
            return res
        if 'move_ids' in fields:
            move_ids = self.pool.get('stock.move').browse(cr, uid, move_ids, context=context)

            # Lanzamos una excepción si alguna dirección es diferente
            for m in move_ids:
                if id_address == False:
                    id_address = m.address_id.id
                if id_warehouse == False:
                    id_warehouse = m.warehouse_id.id
                if m.address_id.id != id_address:
                    raise orm.except_orm(_('Error'), _('Destination address of moves must be the same.'))
                if m.warehouse_id.id != id_warehouse:
                    raise orm.except_orm(_('Error'), _('Warehouse of moves must be the same.'))
            moves = [self._partial_move_for(cr, uid, m) for m in move_ids if m.state not in ('cancel')]
            res.update(move_ids=moves)

        return res

    def _get_action_view(self,cr,uid,ids,move_type,picking_id,context=None):
        """ Devuelve una accion para que al ponerla en el return se abra la vista de albaranes
        mostrando solo el albarán picking_id en función del tipo que sea (salida, entrada,interno)"""
        if context == None: context = {}
        view_name = 'stock.picking.out.form'
        if move_type == 'in':
            view_name = 'stock.picking.in.form'
        if move_type == 'internal':
            view_name = 'stock.picking.form'
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[('name','=',view_name),('model','=','stock.picking'),('inherit_id','=',False)])[0]
        dicc_view =  {
            'name':_("Stock Picking OUT"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'stock.picking',
            'res_id': picking_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': '[]',
            'context': context,
        }
        return dicc_view

    def to_pick(self, cr, uid, ids, context=None):
        """ Albarana los movimientos pasados al asistente, pudiendo modificarse las cantidades
        y actualiza los movimientos originales, restandoles la cantidad necesaria si se dá el caso"""
        if context==None:
            context={}
        wizard = self.browse(cr,uid,ids[0])
        date = False
        id_address = False
        move_type = 'out'
        create_ids = [] #lista de los ids de los movimientos a los que le asignaremos el albarán

        # Recorremos los movimientos a albaranar, averiguando la fecha del movimiento mayor
        # (que será la que ponemos en el albarán) y el tipo. Rellenamos la lista create_ids
        # con los ids de los movimientos a albaranar posteriormente
        origins = set()
        for move in wizard.move_ids:
            if move.move_id.sale_line_id:
                origins.add(move.move_id.sale_line_id.order_id.name)
            if date == False :
                id_address = move.move_id.address_id.id
                date = datetime.strptime(move.move_id.date_expected,"%Y-%m-%d %H:%M:%S")
            # La fecha prevista de los albaranes creados,debe ser la fecha prevista mayor de todos los movimientos.
            if datetime.strptime(move.move_id.date_expected,"%Y-%m-%d %H:%M:%S") > date:
                date = datetime.strptime(move.move_id.date_expected,"%Y-%m-%d %H:%M:%S")
            if move.location_id.usage in ['customer','supplier']:
                move_type = 'in'
            elif move.location_id.usage == 'internal' and move.location_dest_id.usage == 'internal':
                move_type = 'internal'
            if move.quantity > move.move_id.product_qty:
                raise orm.except_orm(_('Error'), _("Quantity can't be higer than the original one."))
            # si las cantidades coinciden, se añade el id a la lista de movimientos a asignar el albarán
            if move.quantity == move.move_id.product_qty:
                create_ids.append(move.move_id.id)
            # en caso contrario se le resta la cantidad al movimiento original, y se crea un nuevo movimiento
            # copia del original salvo lo que definimos en el vals (que son los valores que ponemos en el asistente)
            else:
                move.move_id.write({'product_qty':move.move_id.product_qty - move.quantity,
                                    'product_uos_qty':move.move_id.product_qty - move.quantity
                                    })
                vals = {
                    'product_id' : move.product_id.id,
                    'product_qty' : move.quantity,
                    'product_uos_qty' : self.pool.get('product.uom')._compute_qty(cr,uid,move.move_id.product_uom.id,move.quantity,move.move_id.product_uos.id), #para que al pasar de albarán a factura, mantenga la qty original
                    'product_uom' : move.product_uom.id,
                    'location_id' : move.location_id.id,
                    'location_dest_id' : move.location_dest_id.id,
                    'prodlot_id' : move.prodlot_id.id,
                    'state' : move.move_id.state
                }
                create_ids.append(self.pool.get('stock.move').copy(cr, uid, move.move_id.id, vals, context=context))
            #FIXME this is for compatibity with the addon for multiple warehouse selecion from orders
            if hasattr(move.move_id, 'warehouse_id') and move.move_id.warehouse_id:
                warehouse_id = move.move_id.warehouse_id.id
            else:
                warehouse_id = False

        # creamos la cabecera del albarán
        values = {
            'address_id': id_address,
            'min_date': date,
            'invoice_state': '2binvoiced',
            'type': move_type,
            'origin': ",".join(list(origins))
        }
        picking_obj = self.pool.get('stock.picking')

        picking_id = picking_obj.create(cr, uid, values, context=context)

        #FIXME this is for compatibity with the addon for multiple warehouse selecion from orders
        if hasattr(picking_obj.browse(cr, uid, picking_id), 'warehouse_id'):
            picking_obj.write(cr, uid, picking_id, {'warehouse_id': warehouse_id}, context=context)

        # Asignamos los movimientos anteriores (los de create_ids) al albarán recien creado
        self.pool.get('stock.move').write(cr, uid, create_ids, {'picking_id':picking_id}, context=context)
        wf_service = netsvc.LocalService("workflow")
        # Cambiamos el workflow del albarán a assigned con la señal buttom_confirm
        wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        return wizard._get_action_view(move_type, picking_id, context=context) # devolvemos vista tree solo del albarán creado en función de su tipo

