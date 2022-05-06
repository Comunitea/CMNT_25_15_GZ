from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"




class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    amt_to_invoice = fields.Monetary(string='Amount To Invoice', compute='_compute_invoice_amount', compute_sudo=True, store=True)
    amt_invoiced = fields.Monetary(string='Amount Invoiced', compute='_compute_invoice_amount', compute_sudo=True, store=True)

    @api.depends('qty_received', 
                 'price_subtotal',
                 'state',
                 'invoice_lines',
                 'invoice_lines.price_total',
                 'invoice_lines.invoice_id',
                 'invoice_lines.invoice_id.state',
                 'invoice_lines.invoice_id.refund_invoice_ids',
                 'invoice_lines.invoice_id.refund_invoice_ids.state',
                 'invoice_lines.invoice_id.refund_invoice_ids.amount_total')
    def _compute_invoice_amount(self):
        ## COPIA DEL SALE ORDER LINE ADAPTADO A COMPRAS
        refund_lines_product = self.env['account.invoice.line']
 
        for line in self:
            # Invoice lines referenced by this line
            invoice_lines = line.invoice_lines.filtered(lambda l: l.invoice_id.state in ('open', 'paid') and l.invoice_id.type == 'in_invoice')
            refund_lines = line.invoice_lines.filtered(lambda l: l.invoice_id.state in ('open', 'paid') and l.invoice_id.type == 'in_refund')
            # Refund invoices linked to invoice_lines
            refund_invoices = invoice_lines.mapped('invoice_id.refund_invoice_ids').filtered(lambda inv: inv.state in ('open', 'paid'))
            refund_invoice_lines = (refund_invoices.mapped('invoice_line_ids') + refund_lines - refund_lines_product).filtered(lambda l: l.product_id == line.product_id)
            if refund_invoice_lines:
                refund_lines_product |= refund_invoice_lines
            # If the currency of the invoice differs from the sale order, we need to convert the values
            if line.invoice_lines and line.invoice_lines[0].currency_id \
                    and line.invoice_lines[0].currency_id != line.currency_id:
                invoiced_amount_total = sum([inv_line.currency_id.with_context({'date': inv_line.invoice_id.date}).compute(inv_line.price_total, line.currency_id)
                                             for inv_line in invoice_lines])
                refund_amount_total = sum([inv_line.currency_id.with_context({'date': inv_line.invoice_id.date}).compute(inv_line.price_total, line.currency_id)
                                           for inv_line in refund_invoice_lines])
            else:
                invoiced_amount_total = sum(invoice_lines.mapped('price_total'))
                refund_amount_total = sum(refund_invoice_lines.mapped('price_total'))
            
            total_sale_line = (line.price_total / (line.product_qty ) * line.qty_received) if line.product_qty > 0 else 0.0
            line.amt_invoiced = invoiced_amount_total - refund_amount_total
            line.amt_to_invoice = (total_sale_line - invoiced_amount_total) if line.state in ['purchase', 'done'] else 0.0