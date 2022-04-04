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
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_is_zero, float_compare
from datetime import date, timedelta
import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_default_mts_rule_id(self, location_id, values):
        wh_id =  values['warehouse_id']
        domain = [('action', '=', 'move')]
        if wh_id:
            domain += [('warehouse_id', '=', wh_id.id)]
        ctx = self._context.copy()
        ctx.update(rule_domain=domain)
        rule_id = self.env['procurement.group'].with_context(ctx)._get_rule(self, location_id, values)
        return rule_id and rule_id[0] or False

    def get_default_mto_rule_id(self, location_id, values):
        wh_id =  values['warehouse_id']
        ## Busco una regla en el producto buy o manufacture 
        pull_id = self.route_ids.mapped('pull_ids').filtered(lambda x: x.warehouse_id == wh_id and x.action in ['buy', 'manufacture'])
        if pull_id:
            action = pull_id[0].action
        else:
            raise ValidationError (_('Product %s need buy o manufacture  default route'))
        
        if pull_id[0].location_id == location_id:
            ## Si la regla del producto ya es capaz de abastecer esa ubicacion, ya la devuelvo
            return pull_id
        
        ## si no, busco una regla que lance un aprovisionamiento para location_id, 
        ## y que el abastecimiento posible sea el action definido en producto
        domain = [
            ('procure_method', '=', 'make_to_order'), 
            ('warehouse_id', '=', wh_id.id), 
            ('action', '=', 'move'), 
            ('location_id', '=', location_id.id)]
        rule_ids = self.env['procurement.rule'].search(domain)
        for rule_id in rule_ids:
            location_src_id = rule_id.location_src_id
            pull_domain = [('location_id', '=', location_src_id.id), ('warehouse_id', '=', wh_id.id), ('action', '=', action) ]
            rule_id = self.env['procurement.rule'].search(pull_domain)
            if rule_id:
                return rule_id[0]
        
        raise ValidationError (_('Product %s need buy o manufacture default rule'))

        """
        product_rule_id = self.route_ids.mapped('pull_ids').filtered(lambda x: x.warehouse_id == wh_id and x.action in ['buy', 'manufacture'])
        wh_id =  values['warehouse_id']
        domain = [('action', '=', 'move')]
        if wh_id:
            domain += [('warehouse_id', '=', wh_id.id)]
        ctx = self._context.copy()
        ctx.update(rule_domain=domain)
        return self.env['procurement.group'].with_context(ctx)._get_rule(self, location_id, values)
        """