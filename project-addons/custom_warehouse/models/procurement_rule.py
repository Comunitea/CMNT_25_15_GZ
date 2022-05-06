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
from odoo.tools.float_utils import float_is_zero, float_compare
from datetime import date, timedelta
from odoo.osv import expression
import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)
               


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def _search_rule(self, product_id, values, domain):
        return super()._search_rule(product_id=product_id, values=values, domain=domain)

        if self._context.get('rule_domain', False):
            domain = self._context['rule_domain'] + domain
        Pull = self.env['procurement.rule']
        res = self.env['procurement.rule']
        route_ids = values.get('route_ids', False)
        warehouse_id = values.get('warehouse_id', False)
        if warehouse_id and route_ids and route_ids.warehouse_ids and warehouse_id not in route_ids.warehouse_ids :
            raise ValidationError ("Warehouse %s not in %s route warehouses"%(warehouse_id.name, route_ids.mapped('name')))

