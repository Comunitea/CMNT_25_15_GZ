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
from datetime import date, timedelta
import logging
_logger = logging.getLogger(__name__)

class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def _search_rule(self, product_id, values, domain):
        import pdb; pdb.set_trace()
        if self._context.get('rule_domain', False):
            domain = self._context['rule_domain'] + domain
        return super()._search_rule(product_id=product_id, values=values, domain=domain)

class ProcurementRule(models.Model):

    _inherit = "procurement.rule"

    @api.multi
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, values, po, supplier):
        overprocess_by_supplier = False
        if supplier.min_qty > 0:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(product_qty, supplier.min_qty, precision_digits=precision) == -1:
                _logger.info("Update product qty (%s) because supplier min qty (%s)".format(product_qty, supplier.min_qty))
                product_qty = supplier.min_qty
                overprocess_by_supplier = True
        res = super()._prepare_purchase_order_line(product_id=product_id,
                                                   product_qty=product_qty,
                                                   product_uom=product_uom,
                                                   values=values,
                                                   po=po,
                                                   supplier=supplier)
        res['overprocess_by_supplier'] = overprocess_by_supplier
        return res

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values, group_id):
        result = super()._get_stock_move_values(product_id, product_qty,
                                                product_uom, location_id, name,
                                                origin, values, group_id)
        if values.get('sale_line_id', False):
            line = self.env['sale.order.line'].browse(values['sale_line_id'])
            result['destination_code_id'] = line.destination_code_id
        return result