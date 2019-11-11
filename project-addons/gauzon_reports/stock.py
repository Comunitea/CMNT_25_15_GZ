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

from odoo import models, fields, api


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def _get_sale_notes(self):
        for pick in self:
            sale_ids = []
            for line in pick.move_lines:
                if line.sale_line_id:
                    sale_ids.append(line.sale_line_id.order_id.id)
            sale_ids = list(set(sale_ids))
            pick.sale_note = sale_ids and \
                u"\n".join([x.note for x in self.env['sale.order'].
                            browse(sale_ids) if x.note]) or ""

    sale_note = fields.Text(compute="_get_sale_notes", string='Sale notes')


class StockMove(models.Model):

    _inherit = "stock.move"
    _order = "date_expected desc, sequence asc"

    _columns = {
        'sequence': fields.integer('Sequence', readonly=True)
    }

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(StockMove, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        res['sequence'] = move.sequence
        return res
