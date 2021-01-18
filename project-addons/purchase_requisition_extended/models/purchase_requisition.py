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

from datetime import datetime, timedelta

class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    @api.multi
    def _compute_vendor_ids(self):
        for pr in self:
            pr.vendor_ids = pr.seller_ids.mapped('name')

    @api.multi
    def compute_order_lines_count(self):
        for pr in self:
            pr.order_lines_count = len(pr.purchase_ids.mapped('order_line'))

    group_id = fields.Many2one('procurement.group', 'Procurement Group')
    sale_id = fields.Many2one('sale.order', 'Sale order')
    vendor_ids = fields.Many2many('res.partner', string="Vendors", compute="_compute_vendor_ids")
    seller_ids = fields.Many2many('product.supplierinfo', string="Supplier Info")
    order_lines_count = fields.Float('# Order lines', compute="compute_order_lines_count")

    def create_po_lines(self, purchase_id=False):
        if not purchase_id:
            return False
        partner = purchase_id.partner_id
        payment_term = partner.property_supplier_payment_term_id
        currency = partner.property_purchase_currency_id or self.company_id.currency_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)
        order_lines = []
        seller_ids = self.seller_ids.filtered(lambda x: x.name == partner)
        for seller_id in seller_ids:
            line_ids = self.line_ids.filtered(lambda x: x.product_id == seller_id.product_id or x.product_id.product_tmpl_id == seller_id.product_tmpl_id)
            for line in line_ids:
                order_date = fields.Datetime.from_string(line.schedule_date)
                min_order_date = fields.Datetime.from_string(fields.Datetime.now()[:10]) + timedelta(days=seller_id.delay)
                order_date = fields.Datetime.from_string(line.schedule_date)

                po_order_date = fields.Datetime.to_string(max(order_date, min_order_date))


                # Compute name
                product_lang = line.product_id.with_context({
                    'lang': partner.lang,
                    'partner_id': partner.id,
                })
                name = product_lang.display_name
                if product_lang.description_purchase:
                    name += '\n' + product_lang.description_purchase

                # Compute taxes
                if fpos:
                    taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(
                        lambda tax: tax.company_id == self.company_id)).ids
                else:
                    taxes_ids = line.product_id.supplier_taxes_id.filtered(
                        lambda tax: tax.company_id == self.company_id).ids

                # Compute quantity and price_unit
                seller_qty = seller_id.min_qty
                line_qty = line.product_qty
                if seller_qty > line_qty:
                    qty = seller_qty
                else:
                    qty = line_qty

                if line.product_uom_id != line.product_id.uom_po_id:
                    product_qty = line.product_uom_id._compute_quantity(qty, line.product_id.uom_po_id)
                    price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
                else:
                    product_qty = qty
                    price_unit = seller_id.price
                #if self.type_id.quantity_copy != 'copy':
                #    product_qty = 0
                # Compute price_unit in appropriate currency
                if self.company_id.currency_id != currency:
                    price_unit = self.company_id.currency_id.compute(price_unit, currency)

                # Create PO line
                order_line_values = line._prepare_purchase_order_line(
                    name=name, product_qty=product_qty, price_unit=price_unit,
                    taxes_ids=taxes_ids)
                order_line_values['purchase_requisition_line_id'] = line.id
                order_line_values['date_planned'] = po_order_date
                order_line_values['date_need'] = fields.Datetime.to_string(order_date)
                order_line_values['qty_need'] = line.product_qty
                order_line_values['seller_id'] = seller_id.id
                print(order_line_values)
                order_lines.append((0, 0, order_line_values))
        purchase_id.order_line = order_lines


    @api.multi
    def action_view_order_lines(self):
        lines = self.mapped('purchase_ids').mapped('order_line')
        action = self.env.ref('purchase.action_purchase_line_product_tree').read()[0]
        res = self.env.ref('purchase_requisition_extended.purchase_order_line_tree_pre', False)
        action['views'] = [(res and res.id or False, 'tree')]
        action['domain'] = [('id', 'in', lines.ids)]

        return action

    def create_purchase_orders(self):
        self.ensure_one()
        po_ids = self.env['purchase.order']
        sale_id = self.sale_id
        for partner in self.vendor_ids:
            po_vals = {'partner_id': partner.id,
                       'requisition_id': self.id,
                       'group_id': self.group_id.id,
                       'sale_id': sale_id and sale_id.id or False}
            po = self.env['purchase.order'].create(po_vals)
            po.requisition_id = self.id
            #po.date_planned = self.date

            po_ids |= po
        po_message = "<li><a href=# data-oe-model=purchase.requisition data-oe-id=%d>%s</a></li>" % (self.id, self.name)
        message = _("Next purchase orders has been created from purchase requisition %s</br><ul>")% po_message
        for po in po_ids:
            po_message = "<li><a href=# data-oe-model=purchase.order data-oe-id=%d>%s</a></li>" % (
            po.id, po.name)
            message = '{}{}'.format(message, po_message)
            self.create_po_lines(purchase_id = po)
        message = '{}{}'.format(message, "</ul>")
        if sale_id:
            self.sale_id.message_post(message)


    def generate_new_orders(self):
        self.create_purchase_orders()

        return

    @api.multi
    def compute_seller_ids(self):
        for pr in self:
            pr.seller_ids = self.env['product.supplierinfo']
            date = pr.date_end
            line_ids = pr.line_ids
            for line in line_ids:
                product_id = line.product_id
                seller_ids = product_id._select_seller_without_qty(partner_id=False,
                                                        quantity=0,
                                                        date=date and date[:10],
                                                        uom_id=product_id.uom_po_id)
                pr.seller_ids |= seller_ids

    def _prepare_tender_values(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        res = super()._prepare_tender_values(product_id, product_qty, product_uom, location_id, name, origin, values)
        if values.get('group_id', False):
            res['group_id'] = values['group_id'].id
            sale_id = values['group_id'].sale_id
            if sale_id:
                res['sale_id'] = values['group_id'].sale_id.id
        if res['line_ids']:
            res['line_ids'][0][2]['schedule_date'] = values['move_dest_ids'].date_expected
        print("Tender values %s" %res)
        return res


    def _prepare_tender_line_values(self, product_id, product_qty, product_uom, values):
        values = {
                'requisition_id': self.id,
                'product_id': product_id.id,
                'product_uom_id': product_uom.id,
                'product_qty': product_qty,
                'move_dest_id': values.get('move_dest_ids') and values['move_dest_ids'][0].id or False,
                'schedule_date': values['move_dest_ids'].date_expected

        }
        print (values)
        return values
    @api.multi
    def action_in_progress(self):
        super().action_in_progress()
        self.compute_seller_ids()

