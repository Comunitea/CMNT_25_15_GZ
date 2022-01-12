# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class StockPicking(models.Model):

    _inherit = "stock.picking"

    num_contract = fields.Char("Contract Number", size=128)
    edi_docs = fields.One2many("edi.doc", "picking_id", "Documentos EDI", copy=False)


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _get_sale_line_history(self):
        for move in self:
            if move.sale_line_id:
                move.sale_line_history_id = move.sale_line_id.id
            else:
                self.env.cr.execute(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='stock_move' and (column_name='sale_line_id' or column_name='openupgrade_legacy_8_0_sale_line_id')"
                )
                data = self.env.cr.fetchone()
                if data and data[0]:
                    self.env.cr.execute(
                        "select %s from stock_move where id = %s" % (data[0], move.id)
                    )
                    data2 = self.env.cr.fetchone()
                    if data2 and data2[0]:
                        move.sale_line_history_id = data2[0]

    acepted_qty = fields.Float(
        "Cantidad aceptada", readonly=True, digits=dp.get_precision("Product UoM")
    )
    rejected = fields.Boolean("Rechazado")
    sale_line_history_id = fields.Many2one(
        "sale.order.line", compute="_get_sale_line_history"
    )

    def _assign_picking(self):
        res = super()._assign_picking()
        for pick in self.mapped("picking_id").filtered("sale_id"):
            pick.write(
                {"num_contract": pick.sale_id.num_contract, "note": pick.sale_id.note}
            )
        return res
