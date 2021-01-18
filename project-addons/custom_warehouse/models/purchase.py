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
from odoo.tools.float_utils import float_is_zero, float_compare

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    overprocess_by_supplier = fields.Boolean('Overprocess by supplier min qty. Exceed must go to stock', default=False)

    def _make_po_select_supplier(self, values, suppliers):
        """ Method intended to be overridden by customized modules to implement any logic in the
            selection of supplier.
        """
        return suppliers[0]

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking)
        for val in res:
            val['overprocess_by_supplier'] = self.overprocess_by_supplier
        return res

