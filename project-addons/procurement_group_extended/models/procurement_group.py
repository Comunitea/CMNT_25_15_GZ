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


PICKING_STATES = [('draft', 'Borrador'), ('in_progress', 'En progreso'), ('done', 'Realizado')]

class ProcurementGroup(models.Model):
    _inherit = "procurement.group"
    
    @api.multi
    def compute_show_confirm_sale(self):
        self.ensure_one()
        self.show_confirm_sale = self.sale_ids and any(x.state in ['draft', 'sent'] for x in self.sale_ids)

    @api.multi
    def compute_picking_state(self):
        for group in self:
            picking_ids = group.picking_ids.filtered(lambda x: x.state != 'cancel')
            if not picking_ids:
                state = 'draft'
            elif any(x.state not in ['draft', 'done', 'locked'] for x in picking_ids):
                state = 'in_progress'
            elif all(x.state in ['done', 'locked'] for x in picking_ids):
                state = 'done'
            else:
                state = 'draft'
            group.picking_state = state
    
    @api.multi
    def get_purchase_ids(self):
        for group in self:
            po_domain = [('origin', 'ilike', group.name)]
            group.purchase_ids = self.env['purchase.order'].search(po_domain)

    sale_ids = fields.One2many('sale.order', 'procurement_group_id', string="Ventas", domain=[('state', '!=', 'cancel')])
    purchase_ids = fields.One2many('purchase.order', string="Compras",compute="get_purchase_ids")
    picking_ids = fields.One2many('stock.picking', 'group_id', string="Albaranes", domain=[('state', '!=', 'cancel')])
    #requisition_id = fields.Many2one('purchase.requisition', string="RQF")
    picking_state = fields.Selection(PICKING_STATES, string="Estado de albaranes", compute=compute_picking_state)
    merge_moves = fields.Boolean("Merge moves", help="If true, merge diferent move lines in same move", default=True)
    show_confirm_sale = fields.Boolean('show_cofirm_sale', compute=compute_show_confirm_sale)
    notes = fields.Text(string='Notes')
    production_ids = fields.One2many('mrp.production', 'procurement_group_id', string="Producciones")

    @api.model
    def run(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        ctx=self._context.copy()
        ctx.pop('rule_domain', None)
        return super(ProcurementGroup, self.with_context(ctx)).run(product_id, product_qty, product_uom, location_id, name, origin, values)

    @api.model
    def _search_rule(self, product_id, values, domain):
        if self._context.get('rule_domain', False):
            domain = self._context['rule_domain'] + domain
        return super()._search_rule(product_id=product_id, values=values, domain=domain)

    @api.multi
    def unlink(self):
        """Para poder borrar"""
        self.mapped('picking_ids').unlink()
        self.mapped('purchase_ids').unlink()
        self.mapped('sale_ids').unlink()
        return super().unlink()

    @api.multi
    def action_confirm(self):
        sales = self.sale_ids.filtered(lambda x: x.state in ['draft', 'sent'])
        for sale in sales:
            sale.action_confirm()
    
    @api.multi
    def action_cancel(self):
        if any(x.state == 'done' for x in self.mapped('picking_ids')):
            raise ValidationError ("Hay albaranes ya realizados. No se puede cancelar el abastecimiento")
        for sale in self.mapped('sale_ids'):
            sale.action_cancel()
        for purchase in self.mapped('purchase_ids'):
            purchase.button_cancel()


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):

        vals = super()._get_stock_move_values(product_id=product_id,
                                              product_qty=product_qty,
                                              product_uom=product_uom,
                                              location_id=location_id,
                                              name=name,
                                              origin=origin,
                                              values=values,
                                              group_id=group_id)
        vals.update({
            'sale_id': values.get('sale_id'),
        })
        return vals


    def _run_move(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        ## Tengo que poner los moves dest ids de mts y mto iguales
        if values.get('move_dest_ids', False) and self.picking_type_id.merge_moves:
            split_rule_id = self.route_id.mapped('pull_ids').filtered(lambda x: x.action == 'split_procurement')
            if split_rule_id.mts_rule_id == self or split_rule_id.mto_rule_id == self:
                ## Busco todos los movimientos del mismo tipo y producto del move de destino, y los añado a move_dest_id
                new_move_dest_id = values['move_dest_ids'][0]
                pick_ids = new_move_dest_id.group_id.mapped('picking_ids').filtered(lambda x: x.picking_type_id == new_move_dest_id.picking_type_id)
                move_dest_ids = pick_ids.mapped('move_lines').filtered(lambda x: x.product_id == product_id and x.state != 'cancel') 
                values['move_dest_ids'] |= move_dest_ids

        return super()._run_move(product_id = product_id,
                                  product_qty = product_qty,
                                  product_uom = product_uom,
                                  location_id = location_id, 
                                  name = name, 
                                  origin = origin, 
                                  values = values)


    def _prepare_mo_vals(self, product_id, product_qty, product_uom,
                         location_id, name, origin, values, bom):
        result = super(ProcurementRule, self)._prepare_mo_vals(
            product_id, product_qty, product_uom, location_id,
            name, origin, values, bom
        )
        result['procure_method'] = self.procure_method
        return result




class PushedFlow(models.Model):
    _inherit = "stock.location.path"
    

    def _prepare_move_copy_values(self, move_to_copy, new_date):
        new_move_vals = super()._prepare_move_copy_values(move_to_copy, new_date)
        if self.propagate and move_to_copy.group_id:
            new_move_vals['group_id'] = move_to_copy.group_id.id
        return new_move_vals
