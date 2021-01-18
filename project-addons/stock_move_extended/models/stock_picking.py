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


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def unchain_move(self, assign=True):
        self.ensure_one()
        for pick in self:
            if pick.state != 'waiting':
                raise ValidationError(_("Picking %s not in 'waiting' state" % pick.name))
            move_orig_ids = pick.env['stock.move']
            pick.move_ids.filtered(lambda x: x.state == 'waiting').unchain_move(False, 'make_to_stock', False, False)
            message = _('Pick %s has been unchained'% pick.name)
            pick.picking_id.message_post(message)
            if assign:
                pick.action_assign()




