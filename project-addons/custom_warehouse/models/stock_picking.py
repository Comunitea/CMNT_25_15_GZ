##############################################################################
#
#    Copyright (C) 2020-TODAY
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

from odoo import models, fields, api, exceptions, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_is_zero, float_compare

class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    def _show_moves_to_stock(self):
        picks = self.env['stock.picking']
        for pick in self.filtered(lambda x: x.state in ('assigned', 'partially_available', 'waiting')):
            if pick.picking_type_id.code == 'customer':
                if pick.move_lines.mapped('move_orig_ids').filtered(lambda x: x.procure_method == 'make_to_order'):
                    pick.show_moves_to_stock
                    continue
            if pick.picking_type_id.code == 'supplier':
                pick.show_moves_to_stock
                continue
        picks.write({'show_moves_to_stock': True})

    destination_code_id = fields.Boolean('Destination code')
    rule_id = fields.Many2one('procurement.rule', 'Procurement Rule', ondelete='restrict', help='The procurement rule that created this stock move')
    show_moves_to_stock = fields.Boolean(compute="show_moves_to_stock")

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.context.get('assign_picking_domain'):
            args += self.env.context.get('assign_picking_domain')
        if self.env.context.get('new_picking'):
            args = [('id', '=', 0)]
        return super(StockPicking, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

    def change_incoming_moves_to_storage(self):
        self.move_lines.change_incoming_moves_to_storage()

    def change_moves_to_stockage(self):
        self.move_lines.change_moves_to_stockage()

