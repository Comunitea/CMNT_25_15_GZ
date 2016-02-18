# -*- coding: utf-8 -*-
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
from openerp import models, fields, api
from openerp.osv import orm

class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    product_sup_code = fields.Char('Supplier Product Code',
                                   compute='_get_product_supplier_code')

    @api.one
    @api.depends('product_id')
    def _get_product_supplier_code(self):
        self.product_sup_code = self.product_id.seller_ids and \
                                self.product_id.seller_ids[0].product_code or ''

class stock_move(orm.Model):

    _inherit = "stock.move"
    # _order = "date_expected desc, sequence asc"
    #
    # _columns = {
    #     'sequence': fields.integer('Sequence', readonly=True)
    # }

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        # res['sequence'] = move.sequence
        res['picking_id'] = move.picking_id.id
        return res


from openerp.osv import fields

class StockPicking(models.Model):

    _inherit = 'stock.picking'


    def _get_sale_id(self, cr, uid, ids, name, args, context=None):
        sale_obj = self.pool.get("sale.order")
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = False
            if picking.group_id:
                sale_ids = sale_obj.search(cr, uid, [('procurement_group_id', '=', picking.group_id.id)], context=context)
                if sale_ids:
                    res[picking.id] = sale_ids[0]
            else:
                move = picking.move_lines and picking.move_lines[0] or False
                if not move:
                    continue
                if move.procurement_id.sale_line_id:
                    res[picking.id] = move.procurement_id.sale_line_id.order_id.id
        return res

    _columns = {
        'sale_id': fields.function(_get_sale_id, type="many2one", relation="sale.order", string="Sale Order"),
    }
