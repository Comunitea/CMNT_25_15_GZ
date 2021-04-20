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
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):

    _inherit = "stock.move"
    
    @api.multi
    def unchain_move(self):
        return True

    @api.multi
    def _unchain_move(self, move_orig_ids=False, procure_method='make_to_stock', assign=True, message=True):
        if not move_orig_ids:
            move_orig_ids = self.env['stock.move']
        else:
            self.ensure_one()
        for move in self:
            if move.state != 'waiting':
                raise ValidationError (_("Move %s not in 'waiting' state" % move.name))
            move.move_orig_ids = move_orig_ids
            if procure_method:
                move.procure_method = procure_method
            if message:
                message = _('Move %s has been unchained'%move.name)
                move.picking_id.message_post(message)
            if assign:
                move._action_assign()

            # tengo que desenlazar todo lo que pueda deembocar en este movimiento, si no al confirmarlo puede que se reescriba
            # si está instlado purchase.requisition
            # busco todos los pedidos de compra que tengan por movimiento de destino este movimiento
            # En compras
            # move_dest_ids = fields.One2many('stock.move', 'created_purchase_line_id', 'Downstream Moves')
            # domain = [('mo')]




