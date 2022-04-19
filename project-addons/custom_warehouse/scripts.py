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
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_is_zero, float_compare
import logging
_logger = logging.getLogger(__name__)


"""
COPIAR Y PEGAR EN PYTHON ODOO

active_db = 'entidades'
session.open(db=active_db)
session.env['product.template']._update_analytic_tag_id_from_stock()
session.env['sale.order']._update_analytic_tag_id_from_product()
session.env['stock.warehouse'].update_warehouse()



"""

class SaleOrder(models.Model):
    _inherit = "sale.order"


    def _update_analytic_tag_id_from_product(self):
        sale_domain = [('state', 'in', ['draft', 'cancel'])]
        sale_pool = self.search(sale_domain)
        _logger.info("\n\nACTUALIZANDO LINEA DE NEGOCIO EN %s VENTAS"%len(sale_pool))
        for sale in sale_pool:
            ## _logger.info("\n\nACTUALIZANDO LINEA DE NEGOCIO LA VENTA %s"%sale.name)
            old_analytic_tag_id = sale.analytic_tag_id
            new_analytic_tag_id = sale.filtered(lambda x: x.analytic_tag_id).mapped('order_line.product_id.analytic_tag_id')
            ## _logger.info(">>>> Según artículos %s"%new_analytic_tag_id)
            if len(new_analytic_tag_id) == 1:
                analytic_tag_id = new_analytic_tag_id
            else:
                analytic_tag_id = old_analytic_tag_id
            if analytic_tag_id and sale.analytic_tag_id != analytic_tag_id:
                sale.analytic_tag_id = analytic_tag_id
                _logger.info("\n\nACTUALIZANDO LINEA DE NEGOCIO LA VENTA: {}\n\n>>>> CAMBIA DE {} A {}\n\n".format(sale.name, old_analytic_tag_id.name, analytic_tag_id.name))

        ## self._cr.commit()



class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _update_analytic_tag_id_from_stock(self):
        _logger.info("\n\nACTUALIZANDO LINEA DE NEGOCIO DE PLANTILLAS ...")
        warehouse_ids = self.env['stock.warehouse'].search([]).sorted(lambda x: 'GENERAL' in x.name)
        _logger.info('Se han encontrado {} almacenes'.format(len(warehouse_ids)))
        for warehouse_id in warehouse_ids:
            stock_location = warehouse_id.lot_stock_id
            tag_id = warehouse_id.analytic_tag_id
            _logger.info('>>>>>>> Almacen: {} con Linea de negocio: {}'.format(warehouse_id.display_name, tag_id.name))
            if not tag_id:
                continue
            domain = [('location_id', 'child_of', stock_location.id), ('product_id.product_tmpl_id.analytic_tag_id', '=', False)]
            template_ids = self.env['stock.quant'].search(domain).mapped('product_id.product_tmpl_id')
            ids = [x.id for x in template_ids]
            _logger.info('>>>>>>> Actualizando a {} Nº: {} plantillas\n\n'.format(tag_id.name, len(template_ids)))
            template_ids.write({'analytic_tag_id': tag_id.id})
            self._cr.commit()
        return


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"
    
    @api.multi
    def update_warehouse(self):
        wh_domain = [('parent_warehouse_id', '!=', False)]
        wh_ids = self.env['stock.warehouse'].search(wh_domain)
        for old_wh_id in wh_ids:
            _logger.info ("MIGRANDO ALMACEN %s a %s"%(old_wh_id.display_name, old_wh_id.parent_warehouse_id.display_name))
            ## La ubicación de stock pasa a ser hija de la ubicación de stock del nuevo almacén
            lot_stock_id = old_wh_id.lot_stock_id
            lot_stock_id.name = lot_stock_id.display_name
            lot_stock_id.location_id = old_wh_id.parent_warehouse_id.lot_stock_id
            ## La ubicación física pasa a ser hija de la ubicación física del nuevo almacén
            view_location_id = old_wh_id.view_location_id
            view_location_id.name = view_location_id.display_name
            view_location_id.location_id = old_wh_id.parent_warehouse_id.view_location_id
            ### Migramos los tipos de movimeintos
            types_domain = [('warehouse_id', '=', old_wh_id.id), ('code', 'in', ['incoming', 'outgoing'])]
            for type_id in self.env['stock.picking.type'].search(types_domain):
                type_id.update_to_new_warehouse()
                ## Lo desactivo
                type_id.active = False
            old_wh_id.active = False
            old_wh_id._Cr.commit()

            

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'


    def get_equivalent_new_loc(self, new_wh_id, location_id):
        if self.code == 'incoming':
            location_id = new_wh_id.lot_stock_id
        if self.code == 'outgoing':
            location_id = new_wh_id.lot_stock_id

    @api.multi
    def update_to_new_warehouse(self, id=False, count=0):

        if not self:
            domain = [('code', 'in', ['incoming', 'outgoing'])]
            if id:
                domain += [('id', '=', id)]
            type_ids = self.search(domain)
        else:
            type_ids = self

        for type_id in type_ids:
            _logger.info("MIGRANDO EL TIPO: %s"%type_id.display_name)
            pick_domain =[('picking_type_id', '=', type_id.id), ('state', 'in', ['draft', 'assigned', 'waiting'])]
            picking_ids = self.env['stock.picking'].search(pick_domain,limit = count)
            new_wh_id = type_id.warehouse_id.parent_warehouse_id
            type_domain = [('warehouse_id', '=', new_wh_id.id), ('code', '=', type_id.code)]
            new_type_id = self.env['stock.picking.type'].search(type_domain, limit=1)
           
            for pick_id in picking_ids:
                try:
                    _logger.info("\n\n>>>>> MIGRANDO EL ALBARAN: %s (%s)"%(pick_id.name, pick_id.state))
                    
                    _logger.info(">>>>> Cambiamos ubicaciones almacén y tipo al albaran: %s"%new_type_id.display_name)
                    pick_id.picking_type_id = new_type_id
                    tag_ids = pick_id.move_lines.mapped('sale_line_id.order_id.analytic_tag_id')
                    if not tag_ids:
                        tag_ids = pick_id.move_lines.mapped('product_id.analytic_tag_id')
                    if tag_ids:
                        tag_id = tag_ids[0]
                    else:
                        tag_id = False    
                    vals = {}
                    if type_id.code == 'incoming':
                        pick_id.location_dest_id = new_wh_id.lot_stock_id
                        vals = {'location_dest_id': new_wh_id.lot_stock_id.id}
                    elif type_id.code == 'outgoing':
                        pick_id.location_id = new_wh_id.lot_stock_id
                        vals = {'location_id': new_wh_id.lot_stock_id.id}
                    ### ESTOS DOS NO SE MIGRAN                    
                    elif type_id.code == 'mrp_operation':
                        vals = {'location_dest_id': new_wh_id.lot_stock_id.id,
                                'location_id': new_wh_id.lot_stock_id.id}
                    elif type_id.code == 'internal':
                        pick_id.location_dest_id = new_wh_id.lot_stock_id
                        pick_id.location_id = new_wh_id.lot_stock_id
                        vals = {'location_dest_id': new_wh_id.lot_stock_id.id,
                                'location_id': new_wh_id.lot_stock_id.id}

                    vals['picking_type_id'] = new_type_id.id
                    vals['warehouse_id'] = new_wh_id.id
                    _logger.info(">>>>> Unreserve ...")
                    pick_id.move_line_ids.unlink()
                    _logger.info(">>>>> Cambiamos ubicaciones, almacén y tipo a los movimientos: %s"%new_type_id.display_name)
                    pick_id.move_lines.write(vals)
                    _logger.info(">>>>> Action assign ...")
                    if pick_id.move_lines:
                        pick_id.action_confirm()
                        pick_id.action_assign()
                    else:
                        pick_id.action_cancel()
                        pick_id.unlink()
                    _logger.info(">>>>> Estado: %s\n\n"%pick_id.state)
                except:
                    _logger.info("\n\n >>>>> ERROR: %s\n\n"%pick_id.name)


            self._cr.commit()

