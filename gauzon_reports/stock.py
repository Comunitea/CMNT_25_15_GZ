# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra$ <omar@pexego.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp.osv import orm, fields
import time
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

class stock_picking(orm.Model):

    _inherit = "stock.picking"

    def _get_sale_notes(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for pick in self.browse(cr, uid, ids):
            sale_ids = []
            for line in pick.move_lines:
                if line.sale_line_id:
                    sale_ids.append(line.sale_line_id.order_id.id)
            sale_ids = list(set(sale_ids))
            res[pick.id] = sale_ids and u"\n".join([x.note for x in self.pool.get('sale.order').browse(cr, uid, sale_ids) if x.note]) or ""

        return res

    _columns = {
        'sale_note': fields.function(_get_sale_notes, method=True, type="text", string='Sale notes', readonly=True),
    }

    def _invoice_line_hook(self, cr, uid, move_line, invoice_line_id):
        res = super(stock_picking, self)._invoice_line_hook(cr, uid, move_line, invoice_line_id)
        self.pool.get('account.invoice.line').write(cr, uid, [invoice_line_id], {'sequence': move_line.sequence,
                                                                                  'picking_id': move_line.picking_id.id})

        return res


class stock_move(orm.Model):

    _inherit = "stock.move"
    _order = "date_expected desc, sequence asc"

    _columns = {
        'sequence': fields.integer('Sequence', readonly=True)
    }


class stock_partial_picking(orm.TransientModel):
    _inherit = "stock.partial.picking"

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_partial_picking, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        if not picking_ids or (not context.get('active_model') == 'stock.picking') \
            or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        picking_id, = picking_ids
        if 'picking_id' in fields:
            res.update(picking_id=picking_id)
        if 'move_ids' in fields:
            picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
            move_ids = [x.id for x in picking.move_lines]
            move_ids = self.pool.get('stock.move').search(cr, uid, [('id', 'in', move_ids)], order="sequence asc")
            move_ids = self.pool.get('stock.move').browse(cr, uid, move_ids)
            moves = [self._partial_move_for(cr, uid, m) for m in move_ids if m.state not in ('done','cancel')]
            res.update(move_ids=moves)
        if 'date' in fields:
            res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        return res


class stock_partial_picking_line(orm.TransientModel):

    _inherit = "stock.partial.picking.line"

    def _get_supplier_code(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = ""
            if line.move_id.purchase_line_id:
                results = self.pool.get('product.supplierinfo').search(cr, uid, [('name', '=', line.move_id.purchase_line_id.order_id.partner_id.id),('product_id', '=', line.product_id.product_tmpl_id.id),('product_code', '!=', False)])
                if results:
                    info = self.pool.get('product.supplierinfo').browse(cr, uid, results[0])
                    res[line.id] = info.product_code or ""

        return res

    _columns = {
        'supplier_code': fields.function(_get_supplier_code, method=True, string="Supplier code", readonly=True, type="char", size=125)
    }

