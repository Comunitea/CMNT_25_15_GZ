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

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
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

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _compute_lines_info(self):
        for po in self:
            activas = len(po.order_line.filtered(lambda x: x.state != 'cancel'))
            po.lines_info = '%d/%d'%(activas,  len(po.order_line))

    lines_info = fields.Char("Líneas", compute=_compute_lines_info)

    @api.multi
    def action_cw_back_to_draft(self):
        for po in self.filtered(lambda x: x.state == 'cancel'):
            po.button_draft()

    @api.multi
    def action_cw_cancel_purchase(self):
        not_canceled = self.env['purchase.order']
        for po in self.filtered(lambda x: x.state != 'cancel'):
            if any(po.order_line.filtered(lambda x: x.state != 'cancel')):
                not_canceled |= po
            else:
                po.button_cancel()
        if not_canceled:
            _logger.info ('Los albaranes %s no se han podido cancelar'%not_canceled.mapped('name'))
        

