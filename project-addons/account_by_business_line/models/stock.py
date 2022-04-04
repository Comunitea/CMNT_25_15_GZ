from odoo import api, models, fields


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    ## Ya no es necesario pero se mantiene por si acaso.
    analytic_tag_id = fields.Many2one("account.analytic.tag", "Business line",
                                      domain=[('is_business_line', '=', True)])


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_warehouse_id(self):
        ## al tener ubicaciones y sububicaciones tiene que se arí ...
        def get_parents(location_id):
            location_ids = location_id
            while location_id.location_id:
                location_ids |= location_id.location_id
                location_id = location_id.location_id
            return location_ids

        warehouse_id = self.picking_type_id and self.picking_type_id.warehouse_id or False
        if not warehouse_id:
            if self._is_in():
                location_id = self.location_dest_id
            elif self._is_out():
                location_id = self.location_id
            warehouse_id = self.env['stock.warehouse'].\
                    search([('lot_stock_id', 'in', get_parents(location_id).ids)], limit=1)
        return warehouse_id

    def _account_entry_move(self):
        super()._account_entry_move()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        move = self.sudo()
        if move.sale_line_id and move.sale_line_id.order_id.\
                analytic_account_id:
            if move._is_in():
                sign = 1
                account_id = move.product_id.categ_id.\
                    property_stock_account_input_categ_id.id
            else:
                sign = -1
                account_id = move.product_id.categ_id.\
                    property_stock_account_output_categ_id.id
            if self._context.get('force_valuation_amount'):
                valuation_amount = self._context.get('force_valuation_amount')
            else:
                valuation_amount = move.value
            if sign == -1 and valuation_amount > 0:
                value = sign * valuation_amount
            else:
                value = valuation_amount
            quantity = self.env.context.get('forced_quantity',
                                            move.product_qty)
            quantity = sign * quantity
            date = self._context.get('force_period_date', fields.Date.
                                     context_today(self))
            default_name = move.sale_line_id.order_id.name + ": " + move.name
            self.env['account.analytic.line'].create({
                'name': default_name,
                'date': date,
                'account_id':
                move.sale_line_id.order_id.analytic_account_id.id,
                'tag_ids': [(6, 0, move.sale_line_id.analytic_tag_ids.ids or
                             (move.sale_line_id.order_id.analytic_tag_id and
                              [move.sale_line_id.order_id.
                               analytic_tag_id.id] or []))],
                'unit_amount': quantity,
                'product_id': move.product_id.id,
                'product_uom_id': move.product_id.uom_id.id,
                'amount': value,
                'general_account_id': account_id,
                'ref': move.sale_line_id.order_id.name,
                'user_id': self._uid,
            })

    def _prepare_account_move_line(self, qty, cost, credit_account_id,
                                   debit_account_id):
        res = super()._prepare_account_move_line(qty, cost, credit_account_id,
                                                 debit_account_id)
        if self._context.get('valuation_wh_id'):
            for line in res:
                line[2]['warehouse_id'] = self._context['valuation_wh_id']
        else:
            warehouse_id = self._get_warehouse_id()
            if warehouse_id:
                for line in res:
                    line[2]['warehouse_id'] = warehouse_id.id
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.model
    def create(self, vals):
        if vals.get('state', False) == 'done' and vals.get('move_id'):
            move = self.env['stock.move'].browse(vals['move_id'])
            warehouse_id = move._get_warehouse_id()
            if warehouse_id:
                res = super(StockMoveLine, self.
                            with_context(valuation_wh_id=warehouse_id.id)).\
                    create(vals)
            else:
                res = super().create(vals)
        else:
            res = super().create(vals)
        return res

    @api.multi
    def write(self, vals):
        if 'qty_done' in vals:
            if vals.get('move_id'):
                move = self.env['stock.move'].browse(vals['move_id'])
            else:
                move = self[0].move_id
            warehouse_id = move._get_warehouse_id()
            if warehouse_id:
                res = super(StockMoveLine, self.
                            with_context(valuation_wh_id=warehouse_id.id)).\
                    write(vals)
            else:
                res = super().write(vals)
        else:
            res = super().write(vals)
        return res
