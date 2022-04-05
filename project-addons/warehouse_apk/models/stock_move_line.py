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
                'ack': False
            }
            indice += 1
            res.append(val)
        _logger.info(res)
        return res

    @api.model
    def update_qty_done(self, values):
        id = values.get('id', False)
        inc = values.get('inc', 0)
        qty = values.get('qty', 0)
        return self.browse(id)._update_qty_done(inc, qty)

    def _update_qty_done(self, inc, qty):
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
    def load_multi_serials(self, values):
        sml_id = self.browse(values.get('id'))
        serial_names = values.get('serial_names', []).split('\n')
        use_existing_lots = values.get('use_existing_lots', False)
        use_create_lots = values.get('use_create_lots', False)
        if use_create_lots:
            ## En este caso, lo escribo en lot names
            numero = len(serial_names)
            move_id = sml_id.move_id
            domain = [('move_id', '=', move_id.id), ('lot_name', '=', False)]
            sml_ids = self.search(domain, limit=numero)
            res = []
            inc = 0
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
            return {'moves': res, 'message': 'Se han actualizado %d movimientos' %inc}
        if use_existing_lots:
            numero = len(serial_names)
            move_id = sml_id.move_id
            domain = [('move_id', '=', move_id.id), ('lot_id', '=', False)]
            sml_ids = self.search(domain,)
            res = []
            inc = 0
            for sml_id in sml_ids:
                if serial_names:
                    lot_name = serial_names[0]
                    sml_id.lot_id = self.env['stock.production.lot'].create_if_not_exits(lot_name, sml_id.product_id.id).get_info()
                    sml_id.qty_done = 1
                    sml_id.ack = True
                    serial_names.pop(0)
                    sml_id_res = {'id': sml_id.id, 'qty_done': 1, 'lot_id': sml_id.lot_id.get_info(), 'ack': True}    
                    res.append(sml_id_res)
                    inc += 1
            return {'moves': res, 'message': 'Se han actualizado %d movimientos' %inc}
        return {'message': 'No se ha actualizado nada'}