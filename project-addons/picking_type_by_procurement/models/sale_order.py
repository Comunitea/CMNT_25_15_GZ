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


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def open_type_id(self):
        ctx = self._context.copy()
        if 'orderedBy' in ctx:
            ctx.pop('orderedBy')
        ctx.update({'procurement_group_id': self.procurement_group_id.id})
        action = self.env.ref("stock.stock_picking_type_action").read()[0]
        domain = self.env['stock.picking.type']._get_procurement_domain(self.procurement_group_id.id)
        if self:
            action['domain'] = domain
            action['display_name'] = _("Dashboard: {}".format(self.display_name))
        return action
   
