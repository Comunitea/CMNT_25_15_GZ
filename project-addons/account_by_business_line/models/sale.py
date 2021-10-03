from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    analytic_tag_id = fields.Many2one("account.analytic.tag", "Business line",
                                      domain=[('is_business_line', '=', True)])

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        res = super()._onchange_warehouse_id()
        if self.warehouse_id.analytic_tag_id:
            self.analytic_tag_id = self.warehouse_id.analytic_tag_id.id

        return res

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.analytic_tag_id:
            invoice_vals['main_analytic_tag_id'] = self.analytic_tag_id.id
        return invoice_vals
