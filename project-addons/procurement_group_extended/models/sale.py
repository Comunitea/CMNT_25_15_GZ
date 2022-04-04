##############################################################################
#
#    Copyright (C) 2004-TODAY
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

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    """
    @api.multi
    def _compute_list_picking_ids(self):
        # self.ensure_one()
        for sale in self:
            domain = [('sale_id', '=', sale.id)]
            picking_ids = self.env["stock.move"].search(domain).mapped('picking_id')
            sale.picking_ids = picking_ids
    """
    ## purchase_requisition_id = fields.Many2one(related='group_id.requisition_id')
    ## pasa a ser un grupo calculado
    merge_moves = fields.Boolean(related='procurement_group_id.merge_moves')
    purchase_ids = fields.One2many(related="procurement_group_id.purchase_ids")

    @api.multi
    def action_cancel(self):
        super().action_cancel()
        ### ????
        ##AL CAMBIAR PICKING_IDS, debemos cancelar por movimientos, no por picking_ids
        moves = self.mapped('picking_ids.move_lines').filtered(lambda x: 
            x.state != 'cancel' and 
            x.sale_line_id in self.mapped('order_line'))
        moves._action_cancel()

        ## Intento cancelar las compras asociadas
        
        for sale in self:
            for purchase in sale.mapped('purchase_ids'):
                try:
                    purchase.button_cancel()
                    purchase.unlink()
                except:
                    msg = "Purchase order {} can't be canceled".format(purchase.name)
                    sale.message_post(body=msg)
            mrp_domain = [('procurement_group_id', '=', sale.procurement_group_id.id), ('state', 'not in',['done', 'cancel'])]
            for mrp in self.env['mrp.production'].search(mrp_domain):
                try:
                    mrp.action_cancel()
                    mrp.unlink()
                except:
                    msg = "Mrp order order {} can't be canceled".format(mrp.name)
                    sale.message_post(body=msg)
        
            try:
                sale.requisition_id.action_cancel()
                sale.requisition_id.unlink()
            except:
                msg = "Requistion order {} can't be canceled".format(sale.requistion_id.name)
                sale.message_post(body=msg)
        
        return self.write({'state': 'cancel'})
        ## SI ESTA INSTALADO BATCH PICKING
        ## moves_to_cancel.mapped('picking_id.batch_picking_id').verify_state()
        return True
        ## NO hago el super ya que no puedo cancelar por picking_ids.action_cancel()
        return super().action_cancel()

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.multi
    def _action_launch_procurement_rule(self):
        return super()._action_launch_procurement_rule()

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)
        values['sale_id'] = self.order_id.id
        return values