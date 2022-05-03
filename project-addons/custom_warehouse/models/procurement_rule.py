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


class ProcuremetRoute(models.Model):
    _inherit="stock.location.route"

    @api.multi
    def _clean_multi_company_routes(self):
        routes = self.sudo().env['stock.location.route'].search([])
        #sqls = []
        domain = [('name', '=', 'Almacen de rutas')]
        route_warehouse_id = self.env['procurement.rule'].search(domain)
        if not route_warehouse_id:
            route_warehouse_id = self.create({
                'name': 'Almacen de rutas', 
                'company_id': False})
        for route_id in routes:
            _logger.info("RUTA %s"%route_id.name)
            domain = [('route_id', '=', route_id.id), '|', ('active', '=', False), ('active', '=', True)]
            for rule_id in self.sudo().env['procurement.rule'].search(domain):
                location_id = rule_id.location_src_id
                location_dest_id = rule_id.location_id
                picking_type_id = rule_id.picking_type_id
                type_company = picking_type_id.warehouse_id and picking_type_id.warehouse_id.company_id or False
                loc_company_id = location_id.company_id
                loc_company_id |= location_dest_id.company_id
                if not rule_id.company_id:
                    rule_id.company_id = rule_id.warehouse_id.company_id

                rule_company_id = rule_id.company_id or rule_id.warehouse_id.company_id or rule_id.location_src_id.company_id or False
                _logger.info("Regla %s: %s"%(rule_id.display_name, rule_company_id and rule_company_id.name or 'Sin compañia'))
                if (rule_company_id and route_id.company_id and rule_company_id != route_id.company_id):
                    _logger.info(">>>>> Se actualiza")
                    rule_id.active = False
                    rule_id.route_id=route_warehouse_id
                    # sql = "update procurement_rule set active = 'f' and route_id = null where id = %d"%rule_id.id
                    # sqls += [sql]
                else:
                    _logger.info(">>>>> OK")
        #for sql in sqls:
            #_logger.info(sql)
            #self._cr.execute(sql)
        
        # self._cr.commit()
                


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

