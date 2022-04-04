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

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    
    analytic_tag_id = fields.Many2one("account.analytic.tag", "Business line",
                                      domain=[('is_business_line', '=', True)])

    ## session.open(db='entidades')
    ## session.env['product.template']._update_analytic_tag_id_from_stock()
    def _update_analytic_tag_id_from_stock(self):

        warehouse_ids = self.env['stock.warehouse'].search([]).sorted(lambda x: 'GENERAL' in x.name)
        _logger.info('Se han encontrado los almacenes {}'.format(warehouse_ids.mapped('name')))
        sql_pool = []
        for warehouse_id in warehouse_ids:
            stock_location = warehouse_id.lot_stock_id
            tag_id = warehouse_id.analytic_tag_id
            
            _logger.info('Almacen: {} con Linea de negocio: {}'.format(warehouse_id.display_name, tag_id.name))
            if not tag_id:
                continue
            domain = [('location_id', 'child_of', stock_location.id), ('product_id.product_tmpl_id.analytic_tag_id', '=', False)]
            template_ids = self.env['stock.quant'].search(domain).mapped('product_id.product_tmpl_id')
            ids = [x.id for x in template_ids]
            _logger.info('Actualizando a {} las plantillas:\n {}'.format(tag_id.name, len(template_ids)))

            if len(ids) == 1:
                sql_pool.append('update product_template set analytic_tag_id = %d where id = %d'%(tag_id.id, template_ids.id))
            elif len(ids) > 1:
                sql_pool.append('update product_template set analytic_tag_id = %d where id in (%s)'%(tag_id.id, ','.join(str(x.id) for x in template_ids)))
            
            ## template_ids.write({'analytic_tag_id': tag_id.id})
        for sql in sql_pool:
            _logger.info("Ejecutando %s"%sql)
            self.env.cr.execute(sql)
        self.env.cr.commit()
        return
        empty_template_ids = [('analytic_tag_id', '=', False)]
        product_ids = self.env['product.product'].search(empty_template_ids)
        lot_stock_ids = warehouse_ids.mapped('lot_stock_id')
        for product_id in product_ids:
            move_domain = [('state', '=', 'done'), ('product_id', '=', product_id.id), ('location_id', 'in', lot_stock_ids.ids)]
            analytic_tag_id = self.env['stock.move'].search(move_domain, limit = 1, order="date desc").mapped('warehouse_id.analytic_tag_id')
            if analytic_tag_id:
                product_id.analytic_tag_id = analytic_tag_id
                _logger.info('Actualindo {} a {}'.format(product_id.display_name, analytic_tag_id.name))