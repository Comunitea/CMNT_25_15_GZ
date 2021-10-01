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
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError

class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    control_ok = fields.Boolean(
        'Q. Control', default=True,
        help="Si está marcado, SE propondrá en los acuerdos de compras")


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"
    
    @api.multi
    def _compute_lines_info(self):
        # import pdb; pdb.set_trace()
        for po in self:
            not_canceled = po.order_line.filtered(lambda x: x.line_state != 'cancel')
            activas = len(not_canceled)
            po.lines_info = '%d/%d'%(activas,  len(po.order_line))
            po.amount_untaxed_not_canceled = sum(x.price_subtotal for x in not_canceled)
    
    sale_id = fields.Many2one('sale.order', string='Sale order')
    lines_info = fields.Char("Líneas", compute=_compute_lines_info)
    amount_untaxed_not_canceled = fields.Float('*Total*', compute=_compute_lines_info)

    @api.multi
    def action_cw_back_to_draft(self):
        for po in self.filtered(lambda x: x.state == 'cancel'):
            po.button_draft()

    @api.multi
    def action_cw_cancel_purchase(self):
        not_canceled = self.env['purchase.order']
        for po in self.filtered(lambda x: x.state != 'cancel'):
            if any(po.order_line.filtered(lambda x: x.state != 'cancel')):
                not_canceled |= po
            else:
                po.button_cancel()
                po.order_line.write({'line_state': 'cancel'})

    """
    @api.multi
    def _get_destination_location(self):
        self.ensure_one()
        if self.sale_id:
            return self.env.ref('stock.stock_location_company').id
        return super()._get_destination_location()
    """

    @api.multi
    def button_approve(self, force=False):
        self.mapped('order_line').filtered(lambda x:x.line_state=='cancel').unlink()
        return super().button_approve(force=False)

class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.multi
    @api.depends('order_id.state')
    def _compute_line_status(self):
        for line in self:
            if line.line_state != 'cancel' or line.state != 'cancel':
                line.line_state = line.state

    date_need = fields.Datetime(string='Date needed')
    qty_need = fields.Float('Qty needed')
    seller_id = fields.Many2one('product.supplierinfo')
    line_state = fields.Selection([
                                    ('draft', 'RFQ'),
                                    ('sent', 'RFQ Sent'),
                                    ('to approve', 'To Approve'),
                                    ('purchase', 'Purchase Order'),
                                    ('done', 'Locked'),
                                    ('cancel', 'Cancelled')
                                    ], string='Status', compute="_compute_line_status", store=True)
    purchase_requisition_line_id = fields.Many2one('purchase.requisition.line')
    lines_info = fields.Char("Líneas", related="order_id.lines_info")
    
    @api.multi
    def action_cw_back_to_draft(self):
        self.ensure_one()
        if self.order_id.state == 'cancel':
            self.order_id.button_draft()

    @api.multi
    def action_cw_cancel_purchase(self):
        self.ensure_one()
        if self.order_id.state != 'cancel':
            if all(self.order_id.order_line.filtered(lambda x: x.state == 'cancel')):
                self.order_id.button_cancel()
                self.order_id.order_line.write({'line_state': 'cancel'})

    @api.multi
    def action_reconfirm_self(self):
        for line in self:
            line.line_state = line.state

    def action_open_po(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['res_id'] = self.order_id.id
        res = self.env.ref('purchase.purchase_order_form', False)
        action['views'] = [(res and res.id or False, 'form')]
        action['context'] = {'search_default_todo': 0, 'product_id': self.product_id.id}
        action['target'] = 'new'
        action['flags'] =  {'action_buttons': True,
                            'mode': 'readonly',
                            'options': {'mode': 'readonly'}}
        action['mode'] = 'readonly'
        action['options'] = {'mode': 'readonly'}

        return action

    def action_open_seller(self):
        res = self.env.ref('product.product_supplierinfo_form_view', False)
        view = [(res and res.id or False, 'form')]
        action = {
            'name': _('Seller Properties'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.supplierinfo',
            'views': view,
            'target': 'new',
            'res_id': self.seller_id.id}
        return action

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.context.get('product_id'):
            args += [('product_id', '=', self._context['product_id'])]
        return super().search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):

        ctx = self._context.copy()
        if self.seller_id:
            if self.seller_id.min_qty > self.product_qty:
                raise ValidationError (_('Seller min qty is %s')%self.seller_id.min_qty)
            ctx.update(seller_id=self.seller_id)
        return super(PurchaseOrderLine, self.with_context(ctx))._onchange_quantity()
        if self.seller_id:
            seller = self.seller_id
            #if seller or not self.date_planned:
            #    self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                                 self.product_id.supplier_taxes_id,
                                                                                 self.taxes_id,
                                                                                 self.company_id) if seller else 0.0
            if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
                price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)

            if seller and self.product_uom and seller.product_uom != self.product_uom:
                price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

            self.price_unit = price_unit


    @api.multi
    def action_filter(self):
        self.ensure_one()
        action = self.env.ref('purchase.action_purchase_line_product_tree').read()[0]
        res = self.env.ref('purchase_requisition_extended.purchase_order_line_tree_pre', False)
        action['views'] = [(res and res.id or False, 'tree')]
        action['domain'] = []
        name = ''
        context = eval(action['context'])
        pr_id = self.order_id.requisition_id
        if pr_id:
            action['domain'] += [('order_id', 'in', pr_id.purchase_ids.ids)]
        for field in ['product_id', 'partner_id', 'order_id', 'line_state']:
            key = 'search_default_' + field
            active_field = self._context.get('active_field', False)
            if field == 'line_state':
                field_id = self[field]
            else:
                field_id = self[field] and self[field].id or False
            if active_field == field:
                if not self._context.get(key, False) and field_id:
                    if field != 'line_state':
                        name = '{} - {}'.format(name, self[field].name)
                    action['domain'] += [(field, '=', field_id)]
                    context.update({key: field_id})
                else:
                    context.update({key: False})
            else:
                if self._context.get(key, False) and field_id:
                    if field != 'line_state':
                        name = '{} - {}'.format(name, self[field].name)
                    action['domain'] += [(field, '=', field_id)]
                    context.update({key: field_id})

        action['context'] = context
        action['display_name'] = name or action['name']
        return action

    @api.multi
    def action_confirm_self(self):
        self.ensure_one()
        requisition_id = self.order_id.requisition_id
        if not requisition_id:
            raise ValidationError(_('Only for purchase requisitiom'))
        ## tengo que buscar todas las lineas para esté producto y cancelarlas
        # self.move_dest_ids = self.purchase_requisition_line_id.move_dest_id
        line_ids = requisition_id.purchase_ids.mapped('order_line').filtered(lambda x: x.product_id == self.product_id and self.id != x.id)
        line_ids.write({'line_state': 'cancel'})


    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super()._prepare_stock_moves(picking=picking)
        if self.move_dest_ids:
            new_location_dest_id = self.move_dest_ids.mapped('location_id')
            if picking.location_dest_id != new_location_dest_id:
                picking.location_dest_id = new_location_dest_id

            for vals in res:
                vals['location_dest_id'] = new_location_dest_id.id
        return res
        