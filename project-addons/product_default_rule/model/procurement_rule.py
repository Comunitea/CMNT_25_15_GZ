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


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    action = fields.Selection(
        selection_add=[('product_default', 'Choose from product default')])

    def _run_product_default(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values):

        import pdb; pdb.set_trace()
        ### Esto es una mezcla de MTS + MTO pero con diferencia para fabricar/comprar
        print ("Run product default")
        needed_qty = self.get_mto_qty_to_order(product_id, product_qty,
                                               product_uom, values)

        
        domain = [('action', '=', 'move')]
        ctx = self._context.copy()
        ctx.update(rule_domain=domain)

        mts_rule_id = self.env['procurement.group']._get_rule(product_id, location_id, values)
        print ("Regla MTS: {}".format(mts_rule_id.name))
        ## Hay stock, muevo solo
        if needed_qty == 0.0:
            getattr(mts_rule_id, '_run_%s' % mts_rule_id.action)(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
            return True

        # Busco la primera regla /buy o manufacture
        product_rule_id = product_id.route_ids.mapped('pull_ids').filtered(lambda x: x.action in ['buy', 'manufacture'])
        if product_rule_id[0].action == 'buy':
            action = 'buy'
        else:
            action = 'manufacture'
        group_id = values.get('group_id', False)
        ## Busco una regla para ese almacén, ese ubicación y esa acción
        if group_id:
            domain = [('action', '=', action)]
            ctx = self._context.copy()
            ctx.update(rule_domain=domain)
            rule_id = group_id.with_context(ctx)._get_rule(product_id, location_id, values)
        print ("Regla MTO: {}".format(rule_id.name))
        ## Si no la encuentro, de existencias
        if not rule_id:
            getattr(mts_rule_id, '_run_%s' % mts_rule_id.action)(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
            return True
        if needed_qty == product_qty:
            getattr(rule_id, '_run_%s' % rule_id.action)(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
        else:
            mts_qty = product_qty - needed_qty
            getattr(mts_rule_id, '_run_%s' % mts_rule_id.action)(
                product_id, mts_qty, product_uom, location_id, name, origin,
                values)
            getattr(rule_id, '_run_%s' % rule_id.action)(
                product_id, needed_qty, product_uom, location_id, name,
                origin, values)
        return True
