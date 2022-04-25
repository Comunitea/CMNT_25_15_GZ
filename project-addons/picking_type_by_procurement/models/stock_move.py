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
    _inherit ="stock.picking"
    _order = "priority desc, date asc, id desc"

class StockMove(models.Model):
    _inherit = "stock.move"
        
    def create(self, vals):
        if self._context.get("procurement_group_id"):
            vals['group_id'] = self._context['procurement_group_id']
        return super().create(vals)