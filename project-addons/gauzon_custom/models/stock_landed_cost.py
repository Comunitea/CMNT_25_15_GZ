##############################################################################
#
#    Copyright (C) 2021 Comunitea Servicios Tecnológicos. All Rights Reserved
#    $Omar Castiñeira Saavedra$
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
from odoo import models, _


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    def _create_account_move_line(self, move, credit_account_id,
                                  debit_account_id, qty_out,
                                  already_out_account_id):
        move_lines = super().\
            _create_account_move_line(move, credit_account_id,
                                      debit_account_id, qty_out,
                                      already_out_account_id)
        if qty_out and self.move_id._is_in():
            orig_move_lines = {}
            difference_qty = qty_out
            outs = self.env['account.move.line'].\
                search([('product_id', '=',
                         self.move_id.product_id.id),
                        ('move_id.stock_move_id.location_id.usage',
                         '=', 'internal'),
                        ('move_id.stock_move_id.location_dest_id.usage',
                         '!=', 'internal'),
                        ('debit', '>', 0.0)],
                       order="date desc")
            for move_out in outs:
                if abs(move_out.quantity) < difference_qty:
                    difference_qty -= abs(move_out.quantity)
                    orig_move_lines[move_out] = move_out.quantity
                elif abs(move_out.quantity) >= difference_qty:
                    orig_move_lines[move_out] = difference_qty
                    break

            additional_landed_cost = self.\
                additional_landed_cost * qty_out / self.quantity
            for orig_line in orig_move_lines:
                move = orig_line.move_id.stock_move_id
                if move.sale_line_id and move.sale_line_id.order_id.\
                        analytic_account_id:
                    self.env['account.analytic.line'].create({
                        'name': self.name + ": " +
                        str(orig_move_lines[orig_line]) + _(' already out'),
                        'date': self.cost_id.date,
                        'account_id':
                        move.sale_line_id.order_id.analytic_account_id.id,
                        'tag_ids':
                        [(6, 0, move.sale_line_id.analytic_tag_ids.ids or
                          (move.sale_line_id.order_id.analytic_tag_id and
                           [move.sale_line_id.order_id.analytic_tag_id.id] or
                           []))],
                        'unit_amount': 0.0,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_id.uom_id.id,
                        'amount': -additional_landed_cost,
                        'general_account_id': already_out_account_id,
                        'ref': move.sale_line_id.order_id.name,
                        'user_id': self._uid,
                    })

        return move_lines
