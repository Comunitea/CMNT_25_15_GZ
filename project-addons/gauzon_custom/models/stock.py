##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos. All Rights Reserved
#    $Carlos Lombadía Rodríguez$
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class StockMove(models.Model):

    _inherit = "stock.move"

    prod_supplier_codes = fields.Text("Supplier codes", readonly=True,
                                      related="product_id.supplier_codes")

    @api.multi
    def force_set_qty_done(self):
        field = self._context.get('field', 'product_uom_qty')
        reset = self._context.get('reset', False)
        if reset:
            self.filtered(lambda x: x.quantity_done > 0
                          and x.state != 'done').write({field: 0})
        else:
            for move in self.filtered(lambda x: not x.quantity_done):
                move.quantity_done = move[field]


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.multi
    def force_set_qty_done(self):
        field = self._context.get('field', 'product_uom_qty')
        reset = self._context.get('reset', False)
        if reset:
            self.filtered(lambda x: x.qty_done > 0
                          and x.state != 'done').write({'qty_done': 0})
        else:
            for move in self.filtered(lambda x: not x.qty_done):
                move.qty_done = move[field]


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    all_assigned = fields.Boolean('All assigned', compute='get_all_assigned')
    reserved_availability = fields.Float(
        'Quantity Reserved', compute='compute_picking_qties',
        digits=dp.get_precision('Product Unit of Measure'))
    quantity_done = fields.Float(
        'Quantity Done', compute='compute_picking_qties',
        digits=dp.get_precision('Product Unit of Measure'))
    product_uom_qty = fields.Float(
        'Quantity', compute='compute_picking_qties',
        digits=dp.get_precision('Product Unit of Measure'))
    product_ids_count = fields.Integer('# Products',
                                       compute='_count_product_ids')

    @api.multi
    def _count_product_ids(self):
        for pick in self:
            count = len(pick.move_lines.mapped('product_id'))
            pick.product_ids_count = count

    @api.multi
    def get_all_assigned(self):
        for pick in self:
            pick.all_assigned = not any(x.state in ('partially_available',
                                                    'confirmed')
                                        for x in pick.move_lines)

    @api.multi
    def compute_picking_qties(self):
        for pick in self:
            pick.quantity_done = sum(x.quantity_done for x in pick.move_lines)
            pick.reserved_availability = sum(x.reserved_availability
                                             for x in pick.move_lines)
            pick.product_uom_qty = sum(x.product_uom_qty for x in
                                       pick.move_lines)

    @api.multi
    def force_set_qty_done(self):
        model = self._context.get('model_dest', 'stock.move')
        for picking in self:
            if model == 'stock.move':
                picking.move_lines.force_set_qty_done()
            else:
                picking.move_line_ids.force_set_qty_done()

    @api.multi
    def action_view_product_lst(self):
        self.ensure_one()
        products = self.move_lines.mapped('product_id')
        action = self.env.ref(
            'product.product_normal_action').read()[0]
        if len(products) > 1:
            action['domain'] = [('id', 'in', products.ids)]
        elif len(products) == 1:
            form_view_name = 'product.product_normal_form_view'
            action['views'] = [
                (self.env.ref(form_view_name).id, 'form')]
            action['res_id'] = products.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    to_refund = fields.Boolean(default=True)


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        for line in res.get('product_return_moves', []):
            line[2]['to_refund'] = True
        return res
