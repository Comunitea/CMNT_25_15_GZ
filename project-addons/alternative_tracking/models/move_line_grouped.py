# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

# from odoo.tools.float_utils import float_compare



_logger = logging.getLogger(__name__)


class MoveLineGrouped(models.Model):

    _name = "move.line.grouped"
    _description = "Move line grouped for picking"
    _auto = False
    _rec_name = "name"
    _order = "removal_priority desc, removal_dest_priority"

    def _get_available_serial_ids(self):
        move_line_id = self.env["stock.move.line"].browse(self.id)
        self.available_serial_ids = move_line_id.available_serial_ids

    def _get_lot_ids(self):

        for line in self:
            if line.move_line_ids_str:
                sml_ids = line.move_line_ids_str.split(",")
                sml_ids = self.env["stock.move.line"].browse([int(x) for x in sml_ids])
                line.move_line_ids = sml_ids

            _logger.info(
                "Busco lotes para la línea {} para el box {}".format(
                    line.product_id.display_name, line.loc_dest_name
                )
            )
            if line.product_id.virtual_tracking:
                _lot_ids = line.tracking_lot_ids
            else:
                _lot_ids = line.line_lot_ids
            _logger.info(
                "1º La línea {} para el box {} tienen los lot {}".format(
                    line.product_id.display_name, line.loc_dest_name, _lot_ids
                )
            )
            if _lot_ids:
                # import ipdb; ipdb.set_trace()
                lot_ids = _lot_ids.split(",")
                lot_ids = self.env["stock.production.lot"].browse(
                    [int(x) for x in lot_ids]
                )
                line.lot_ids = lot_ids
                line.lot_ids_string = lot_ids.mapped("name")
                _logger.info(
                    "2º La línea {} para el box {} tienen los lot {}".format(
                        line.product_id.display_name,
                        line.loc_dest_name,
                        line.lot_ids.mapped("name"),
                    )
                )
            line.move_line_id = self.env["stock.move.line"].browse(line.id)

    name = fields.Char("Name")
    move_id = fields.Many2one("stock.move", "Stock Move")
    product_id = fields.Many2one("product.product", "Product")
    picking_id = fields.Many2one("stock.picking", "Picking")
    # NOT BATCH PICKING
    # batch_id = fields.Many2one("stock.picking.batch", "Batch Picking")
    product_uom_qty = fields.Float("Reserved quantity")
    quantity_done = fields.Float("Quantity done")
    track_from_line = fields.Boolean("Track from line")
    virtual_tracking = fields.Boolean("With tracking")
    location_id = fields.Many2one("stock.location", "Src Location")
    loc_name = fields.Char("Loc Name")
    location_dest_id = fields.Many2one("stock.location", "Dest Location")
    loc_dest_name = fields.Char("Dest Loc Name")
    removal_priority = fields.Integer("Removal priority")
    removal_dest_priority = fields.Integer("Dest Removal priority")
    state = fields.Selection(related="move_id.state")
    product_uom = fields.Many2one(related="move_id.product_uom")
    use_existing_lots = fields.Boolean(related="move_id.use_existing_lots")
    available_serial_ids = fields.One2many(
        "stock.production.lot", compute=_get_available_serial_ids
    )
    lot_ids_string = fields.Text("Serial list to add", compute="_get_lot_ids")
    lot_ids = fields.One2many("stock.production.lot", compute="_get_lot_ids")
    line_lot_ids = fields.Text()
    tracking_lot_ids = fields.Text()
    kanban_state = fields.Selection(
        [("to_do", "Blue"), ("done", "Green"), ("doing", "Yellow")],
        string="Kanban State",
        copy=False,
        default="normal",
        required=True,
    )
    move_line_ids_str = fields.Char("Moves from query")
    move_line_ids = fields.Many2many("stock.move.line")

    def _query(self, with_clause="", fields={}, groupby="", from_clause=""):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            CASE WHEN
                sm.track_from_line THEN 'stock.move.line'
                ELSE 'stock.move' END
                AS model,
            min(sml.id) as id,
            sm.name as name,
            sml.move_id as move_id,
            sm.product_id as product_id,
            sml.location_id as location_id,
            sl.name as loc_name,
            sml.location_dest_id as location_dest_id,
            sld.name as loc_dest_name,
            count(lml.lot_id) as factor,
            (sum(sml.product_uom_qty) / greatest(1, count(lml.lot_id)))::integer as product_uom_qty,
            (sum(sml.qty_done) / greatest(1, count(lml.lot_id)))::integer as quantity_done,
            sm.virtual_tracking as virtual_tracking,
            sm.track_from_line as track_from_line,
            sml.removal_priority as removal_priority,
            sml.removal_dest_priority as removal_dest_priority,
            sm.picking_id as picking_id,
            case
                when sum (sml.qty_done) = 0 then 'to_do'
                when sum (sml.qty_done) < sum(sml.product_uom_qty) then 'doing'
                when sum (sml.qty_done) = sum(sml.product_uom_qty) then 'done'
            else
                'to_do'
            end
            as kanban_state,
            array_to_string(array_agg(distinct(sml.id)),',') as move_line_ids_str,
            array_to_string(array_agg(distinct(sml.lot_id)),',') as line_lot_ids,
            array_to_string(array_agg(distinct(lml.lot_id)),',') as tracking_lot_ids
        """
        for field in fields.values():
            select_ += field

        from_ = (
            """
                stock_move_line sml
                join stock_move sm on sm.id = sml.move_id
                join stock_picking sp on sp.id = sm.picking_id
                join stock_location sl on sml.location_id = sl.id
                join stock_location sld on sml.location_dest_id= sld.id
                left join lot_id_move_line_id_rel lml on lml.move_line_id = sml.id
                %s
        """
            % from_clause
        )

        groupby_ = """
            sm.product_id,
            sm.location_id,
            sml.location_dest_id,
            sl.name,
            sld.name,
            sml.location_id,
            sml.move_id,
            sm.track_from_line,
            sm.virtual_tracking,
            sm.name,
            sml.removal_priority,
            sm.picking_id,
            sml.removal_dest_priority %s
        """ % (
            groupby
        )

        return "%s (SELECT %s FROM %s WHERE sm.product_id IS NOT NULL GROUP BY %s)" % (
            with_,
            select_,
            from_,
            groupby_,
        )

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = self._query()
        _logger.info("SQL: %s" % sql)
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s as (%s)""" % (self._table, sql)
        )
