from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class PickingType(models.Model):
    _inherit = 'stock.picking.type'

    app_integrated = fields.Boolean("Show in app", default=False)
    allow_overprocess = fields.Boolean(
        "Overprocess", help="Permitir realizar más cantidad que la reservada"
    )
    icon = fields.Char("Icono")
    default_location = fields.Selection(
        selection=[("location_id", "Origen"), ("location_dest_id", "Destino")],
        string="Tipo de ubicación por defecto",
    )
    need_confirm_product_id = fields.Boolean('Confirma prod antes de cant.?', help="Si está marcado, la aplicación necesitará confimar artículos antes que cambiar las cantidades", default=False)
    need_loc_before_qty = fields.Boolean('Confirma ubic antes de cant.?', help="Si está marcado, la aplicación necesitará confimar ubicaciones antes que cambiar las cantidades", default=False)
    need_location_dest_id = fields.Boolean('Confirma destino?', help="Si está marcado, la aplicación necesitará confimar destino para cada movimiento", default=False)
    need_location_id = fields.Boolean('Confirma origen?', help="Si está marcado, la aplicación necesitará confimar origen para cada movimiento", default=False)
    allow_change_location_id = fields.Boolean('Cambiar origen?', help="Si está marcado, la aplicación permite cambiar origen", default=False)
    allow_change_location_dest_id = fields.Boolean('Cambiar destino?', help="Si está marcado, la aplicación permite cambiar destino", default=False)
    need_confirm_lot_id = fields.Boolean('Confirma Lote?', help="Si está marcado, la aplicación necesitará confimar el lote", default=False)
    next_move_on_qty_done = fields.Boolean('Auto Siguiente', help="Si está marcado, la aplicación saltará al siguiente movimiento una vez todos hechos", default=False)
    validate_on_finish = fields.Boolean('Auto Validación', help="Si está marcado, la aplicación validará automaticamente", defualt=False)
    
    @api.model
    def get_info(self, type = 0):
        self.ensure_one()

        val = {
            'id': self.id,
            'name': self.name,
            'allow_overprocess': self.allow_overprocess,
            'default_location': self.default_location ,
            'allow_change_location_id': self.allow_change_location_id ,
            'allow_change_location_dest_id': self.allow_change_location_dest_id,
            'next_move_on_qty_done': self.next_move_on_qty_done ,
            'validate_on_finish': self.validate_on_finish ,
            'use_existing_lots': self.use_existing_lots,
            'use_create_lots': self.use_create_lots


        }
        return val
    