from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    need_confirm_product_id = fields.Boolean('Confirma prod antes de cant.?', help="Si está marcado, la aplicación necesitará confimar artículos antes que cambiar las cantidades", default=False)
    need_loc_before_qty = fields.Boolean('Confirma ubic antes de cant.?', help="Si está marcado, la aplicación necesitará confimar ubicaciones antes que cambiar las cantidades", default=False)
    need_location_dest_id = fields.Boolean('Confirma destino?', help="Si está marcado, la aplicación necesitará confimar destino para cada movimiento", default=False)
    need_location_id = fields.Boolean('Confirma origen?', help="Si está marcado, la aplicación necesitará confimar origen para cada movimiento", default=False)
    need_confirm_lot_id = fields.Boolean('Confirma Lote?', help="Si está marcado, la aplicación necesitará confimar el lote", default=False)
    removal_priority = fields.Integer("Removal priority", store=True) #compute="compute_removal_priority")
    ack = fields.Boolean("Updated from apk", default=False)
    
    @api.model
    def get_move_lines_info(self, values):
        _logger.info(self._context)
        _logger.info(values)
        domain = values.get('domain', [])
        order = values.get('order', 'removal_priority desc')
        if not domain:
            limit = 25
        else:
            limit = 0
        moves = self.search(domain, order=order, limit=limit)
        _logger.info(moves.mapped('display_name'))
        res = []
        indice = 0
        # default_location = self[0].move_id.picking_type_id.default_location
        ## import pdb; pdb.set_trace()
        for move in moves:
 
            val = {
                'id': move.id,
                'move_id': move.move_id.id,
                'indice': indice,
                'name': move.display_name,
                'product_id': move.product_id.get_info(),
                'tracking': move.product_id.tracking,
                'state': move.return_selection_fields('state'),
                'qty_done': move.qty_done,
                'product_uom_qty': move.product_qty,
                'not_reserved_qty': move.move_id.product_uom_qty - move.move_id.reserved_availability,
                'uom_id': move.product_uom_id.get_info(),
                'location_id': move.location_id.get_info(),
                'location_dest_id': move.location_dest_id.get_info(),
                'lot_id': move.lot_id.get_info(),
                'lot_name': move.lot_name,
                'removal_priority': move.removal_priority,
                'need_confirm_product_id': move.need_confirm_product_id,
                'need_loc_before_qty': move.need_loc_before_qty,
                'need_location_dest_id': move.need_location_dest_id,
                'need_location_id': move.need_location_id,
                'need_confirm_lot_id': move.need_confirm_lot_id,
                'ack': move.ack
            }
            indice += 1
            res.append(val)
        _logger.info(res)
        return res

    @api.model
    def update_qty_done(self, values):
        pick_id = values.get('pick_id')
        qty = values.get('qty', 0)
        id = values.get('id', False)
        inc = values.get('inc', 0)
        if pick_id:
            move_line_ids = self.env['stock.picking'].browse(pick_id).move_line_ids.filtered(lambda x: x.state != 'done')
            if qty == 0:
                move_line_ids.write({'qty_done': 0})
            else:
                for sml_id in move_line_ids:
                    sml_id.qty_done = sml_id.product_uom_qty        
            return {'qty_done': qty}
        return self.browse(id)._update_qty_done(inc, qty)

    def _update_qty_done(self, inc, qty):
        if qty < 0:
            self.qty_done = self.product_uom_qty
        
        allow_overprocess = self.move_id.picking_type_id.allow_overprocess
        qty_done = self.qty_done
        if inc == 0:
            qty_done = qty
        else:
            qty_done += inc
        if qty_done > self.product_uom_qty and not allow_overprocess and self.product_uom_qty:
            self.qty_done = self.product_uom_qty
            return {'qty_done': self.qty_done, 'message': 'No puedes hacer más cantidad de la solicitada'}
        elif qty_done < 0:
            self.qty_done = 0
            return {'qty_done': self.qty_done, 'message': 'No puedes hacer cantidades negativas'}
        else:
            self.qty_done = qty_done
        return {'qty_done': self.qty_done}
    
    @api.model
    def find_lot(self, values):
        res = {}
        
        use_existing_lots = values.get('use_existing_lots', False)
        use_create_lots = values.get('use_create_lots', False)

        name = values.get('name', False)
        product_id = values.get('product_id', False)
        domain = [('product_id', '=', product_id), '|', ('name', '=', name), ('ref', '=', name)]
        lot_id = self.env['stock.production.lot'].search(domain, limit=1)
        if not lot_id and use_create_lots:
            ## No lo creo, si no que escribo lot_name
            return lot_id.create_if_not_exits(name, product_id).get_info()
        if not lot_id:
            return {'message': 'No se ha encontrado el lote %s'%name}
        
        sml_id = self.env['stock.move.line'].browse(values.get('sml_id'))
        if sml_id.state not in ['confirmed', 'assigned', 'partially_available']:
            return {'message': 'Estado incorrecto %s'%sml_id.state}
        quant_domain = [('lot_id', '=', lot_id.id), ('location_id', 'child_of', sml_id.move_id.location_id.id)]
        quant = self.env['stock.quant'].search(quant_domain)
        qty_available = sum(x.quantity - x.reserved_quantity for x in quant)
        if not quant:
            return {'message': 'No se ha encontrado stock para este lote'}
        if len(quant) == 1:
            ### Solo hay un quant posible, lo permito
            res['location_id']= quant.location_id.get_info()
        if len(quant) > 1:
            ### Si hay mas de uno, pongo la ubicación del movimiento, y obligo a leer la nueva ubicación
            res['location_id'] = sml_id.move_id.location_id.get_info()
            res['need_location_id'] = True
        res['lot_id'] = lot_id.get_info()
        res['message'] = 'Cantidad disponible %s'%qty_available
        return res

    @api.model
    def unload_serial_from_moves(self, values):
        sml_id = self.browse(values.get('id'))
        move_id = sml_id.move_id
        
        if move_id.state not in ['partially_available', 'assigned']:
            raise ValidationError ("Sin movimientos donde escribir")

        spl = self.env['stock.production.lot']
        ctx = self._context.copy
        
        if not ml.location_id.should_bypass_reservation():
            ctx.update({'bypass_reservation_update': True})
            Quant = self.env['stock.quant']
            sml_ids = move_id.move_line_ids.filter(lambda x: x.lot_id)
            for sml_id in sml_ids:            
                ##QUITO LA RESERVA PARA EL LOTE Y DEJO EL MOVIMIENTO SIN LOTE, PERO TENG QUE HACERLO YO PARA QUE NO QUITE EL PRODUCT_UOM_QTY NI AFECTE A NADA MAS
                Quant._update_reserved_quantity(sml_id.product_id, sml_id.location_id, -1, lot_id=sml_id.lot_id, package_id=sml_id.package_id, owner_id=sml_id.owner_id, strict=True)
        
        vals = {'lot_id': False, 'qty_done': 0, 'ack': False}
        sml_ids.with_context(ctx).write(vals)
        _logger.info("Se han reseteado los nº de serie para %s"%move_id.display_name)
        return True

    @api.model
    def load_multi_serials(self, values):
        
        sml_id = self.browse(values.get('id'))
        if sml_id.product_id.tracking != 'serial':
            raise ValidationError ("Solo rticulos marcados como serie")
        serial_names = values.get('serial_names', []).split('\n')
        _logger.info("Evaluando Nº Serie: %s"%serial_names)
        use_existing_lots = values.get('use_existing_lots', False)
        use_create_lots = values.get('use_create_lots', False)
        allow_overprocess = values.get('allow_overprocess', False)
        
        Quant = self.env['stock.quant']
        ### Quito los nombres vacíos
        while '' in serial_names: serial_names.remove('')
        orig_serial_names = serial_names
        ## No todco los movimientos que tengan un lote que ya esté en la lista
        move_id = sml_id.move_id

        ctx = self._context.copy()
        import pdb; pdb.set_trace()
        if use_create_lots:
            ## Los lotes que ya están no los toco, solo los marcomo leidos y pongo qty_done a 1
            sml_ids_intocables = move_id.move_line_ids.filtered(lambda x: (x.lot_name and x.ack) or x.lot_name in serial_names)
            sml_ids = move_id.move_line_ids - sml_ids_intocables
            sml_ids_intocables_lots = sml_ids_intocables.mapped('lot_name')
            if sml_ids_intocables:
                sml_ids_intocables.write({'ack': True, 'qty_done': 1})
            ## Quito de la lista de lotes los utilziados
            for lot_name in serial_names:
                if lot_name in sml_ids_intocables_lots:
                    serial_names.remove(lot_name)
                    sml_ids_intocables_lots.remove(lot_name)
            if not sml_ids:
                raise ValidationError ("Todos los movimientos tienen un nº de serie asignado #1")
            res = []
            inc = 0
            for sml_id in sml_ids_intocables:
                sml_id.ack = True
                sml_id.qty_done = 1
                sml_id_res = {'id': sml_id.id, 'qty_done': 1, 'lot_name': sml_id.lot_name, 'ack': sml_id.ack}

            for sml_id in sml_ids:
                if serial_names:
                    lot_name = serial_names[0]
                    sml_id.lot_name = lot_name
                    sml_id.qty_done = 1
                    sml_id.ack = True
                    serial_names.pop(0)
                    sml_id_res = {'id': sml_id.id, 'qty_done': 1, 'lot_name': sml_id.lot_name, 'ack': True}    
                    res.append(sml_id_res)
                    inc += 1

            if serial_names:
                if not allow_overprocess:
                    raise ValidationError("Has introducido %d series de más"%len(serial_names))
                for serial in serial_names:
                    sml_id = sml_ids.copy()
                    sml_id.lot_name = serial
                    sml_id.qty_done = 1
                    sml_id.ack = True
                    sml_id_res = {'id': sml_id.id, 'qty_done': 1, 'lot_name': sml_id.serial, 'ack': True}    
                    res.append(sml_id_res)
                    inc += 1
            return {'moves': res, 'message': 'Se han actualizado %d movimientos' %inc}
        
        if use_existing_lots:
            ## Los lotes que ya están no los toco, solo los marcomo leidos y pongo qty_done a 1
            sml_ids_intocables = move_id.move_line_ids.filtered(lambda x: (x.lot_id and x.ack) or (x.lot_id and x.lot_id.name in serial_names))
            sml_ids = move_id.move_line_ids - sml_ids_intocables
            sml_ids_intocables_lots = sml_ids_intocables.mapped('lot_id.name')
            for sml_id in sml_ids_intocables:
                serial_names.remove(sml_id.lot_id.name)
            res = []
            res_sml = []
            inc = 0
            numero = len(serial_names)
            res_sml = sml_ids_intocables
            inc = 0
            sml_ids.unlink()
            lot_ids = self.env['stock.production.lot'].create_if_not_exits(serial_names, sml_id.product_id.id)
            need = move_id.product_uom_qty - len(sml_ids_intocables)
            if need < len(lot_ids) and not allow_overprocess:
                raise ValidationError ("No se puede hacer mas cantidad de la solictada #2")
            if lot_ids:
                ctx.update({'force_lot_ids': lot_ids})
                move_id.with_context(ctx)._action_assign()
                
            move_id.move_line_ids.write({'ack': True, 'qty_done': 1.0})
            res = []
            if move_id.state != 'assigned':
                move_id._action_assign()
            values = {'domain': [('move_id', '=', move_id.id)]}
            for sml_id in move_id.move_line_ids:
                sml_id_res = {'id': sml_id.id, 'qty_done': sml_id.qty_done, 'lot_id': sml_id.lot_id.get_info(), 'ack': sml_id.ack}    
                res.append(sml_id_res)
            return {'moves': self.get_move_lines_info(values), 'message': 'Se han actualizado %d movimientos' %inc}
        return {'message': 'No se ha actualizado nada'}