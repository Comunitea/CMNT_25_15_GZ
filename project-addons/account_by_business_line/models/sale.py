from odoo import _, models, fields, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    analytic_tag_id = fields.Many2one("account.analytic.tag", "Business line",
                                      domain=[('is_business_line', '=', True)])
    
    @api.onchange('order_lines.product_id')
    def _onchange_product_line(self):
        order_line_at_id = self.order_lines.mapped('product_id.analytic_tag_id')
        if not order_line_at_id:
            return 
        
        if len(order_line_at_id) == 1:
            if self.analytic_tag_id == False:
                self.analytic_tag_id = order_line_at_id

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        
        res = super()._onchange_warehouse_id()
        ## Viene de los artículos
        ## if self.warehouse_id.analytic_tag_id:
        ##     self.analytic_tag_id = self.warehouse_id.analytic_tag_id.id
        return res
    
    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.analytic_tag_id:
            invoice_vals['main_analytic_tag_id'] = self.analytic_tag_id.id
        return invoice_vals

    @api.multi
    def action_confirm(self):
        ## Si intento confirmar y no tengo cuenta analítica intento asignarla según los artículos
        for order in self.filtered(lambda x: not x.analytic_tag_id):
            analytic_tag_id = order.order_line.filtered(lambda x: x.product_id.analytic_tag_id).mapped('product_id.analytic_tag_id')
            if len(analytic_tag_id) == 1:
                order.analytic_tag_id = analytic_tag_id
            else:
                raise ValidationError(_('You must set business line in the order because there is more than one business line in products'))
            
        return super().action_confirm()
