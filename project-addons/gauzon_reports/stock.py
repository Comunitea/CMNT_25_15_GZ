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
                if line.procurement_id.sale_line_id:
                    sale_ids.append(line.procurement_id.sale_line_id.order_id.id)
            sale_ids = list(set(sale_ids))
            res[pick.id] = sale_ids and u"\n".join([x.note for x in self.pool.get('sale.order').browse(cr, uid, sale_ids) if x.note]) or ""

        return res

    _columns = {
        'sale_note': fields.function(_get_sale_notes, method=True, type="text", string='Sale notes', readonly=True),
    }


class stock_move(orm.Model):

    _inherit = "stock.move"
    _order = "date_expected desc, sequence asc"

    _columns = {
        'sequence': fields.integer('Sequence', readonly=True)
    }

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        res['sequence'] = move.sequence
        # res['picking_id'] = move.picking_id.id
        return res
