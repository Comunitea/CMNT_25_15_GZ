# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# from odoo.tools.float_utils import float_compare



_logger = logging.getLogger(__name__)


class StockMoveLocationWizard(models.TransientModel):
    _inherit = "wiz.stock.move.location"

    def _get_move_values(self, picking, lines):
        res = super()._get_move_values(picking, lines)
        res.update(picking_type_id=self.picking_type_id.id)
        return res


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    bypass_tracking = fields.Boolean("By pass tracking")


class StockLocation(models.Model):
    _inherit = "stock.location"


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_available_serial_ids(self):
        spl = self.env["stock.production.lot"]
        for line in self:
            location_id = line.move_id.location_id
            product_id = line.product_id
            ## Los nuemros de serie disponibles son:
            domain = spl.get_domain_for_available_lot_ids(location_id, product_id, strict=False, bom=True)
            
            # Si viene de un mov anterior. 
            
            if line.move_id.procure_method == 'make_to_order':
                # 1. los movimientos no están hechos, entonces esos no:
                move_orig_ids_not_done = line.move_id.move_orig_ids.filtered(lambda x: x.state != 'done').mapped('lot_ids')
                if move_orig_ids_not_done:
                    domain += [('id', 'not in', move_orig_ids_not_done.ids)]
                # 2. Los mov. están hechos y el albarán requiere series.
                move_orig_ids_done = line.move_id.move_orig_ids.filtered(lambda x:x.state=='done' and not x.picking_type_id.bypass_tracking).mapped('lot_ids')
                if move_orig_ids_not_done:
                    domain += [('id', 'in', move_orig_ids_done.ids)]
                # 3. Los mov. están hechos pero bypass_tracking
                # En este caso los numeros de serie deben estar de donde sale el movimiento original
                move_orig_ids_done_with_bypass = line.move_id.move_orig_ids.filtered(lambda x:x.state=='done' and x.picking_type_id.bypass_tracking)
                if move_orig_ids_done_with_bypass:
                    location_id += move_orig_ids_done_with_bypass[0].location_id
                    domain = spl.get_domain_for_available_lot_ids(location_id, product_id, strict=False, bom=True)
            ## Si el movimiento es de retorno:
            if line.move_id.origin_returned_move_id:
                domain +=[('id', 'in', line.move_id.origin_returned_move_id.lot_ids.ids)]
                
            line.available_serial_ids = self.env["stock.production.lot"].search(domain)

    """@api.model
    def _get_domain_for_lot_ids(self, product_id):

        product_domain = [("product_id", "=", product_id.id)]
        ids_domain = []
        location_domain = []
        # Si es un movimeinto de retorno y tiene lotes,
        # O si le precede un movimiento >>>
        # siempre en los que hay en el movimiento anterior
        move_orig_ids = self.move_id.origin_returned_move_id | self.move_id.move_orig_ids
        if move_orig_ids:
            ids_domain = [("id", "in", move_orig_ids.mapped("lot_ids").ids)]
        location_domain += ["|", ("location_id", '=', False), ("location_id", "child_of", self.move_id.location_id.id)]
        domain = product_domain + ids_domain + location_domain
        return domain
    """
    lot_ids = fields.Many2many(
        comodel_name="stock.production.lot",
        relation="lot_id_move_line_id_rel",
        column1="move_line_id",
        column2="lot_id",
        string="Lots",
        # domain=_get_domain_for_lot_ids,
        copy=False,
    )

    available_serial_ids = fields.One2many(
        "stock.production.lot", compute=_get_available_serial_ids
    )
    lot_ids_string = fields.Text("Serial list to add")
    virtual_tracking = fields.Boolean(related="move_id.virtual_tracking")
    track_from_line = fields.Boolean(related="move_id.track_from_line")
    removal_priority = fields.Integer(string="Removal priority")
    removal_dest_priority = fields.Integer(string="Removal dest priority")

    # Estos campos están definidos así en la 12
    picking_type_use_create_lots = fields.Boolean(related='move_id.picking_type_id.use_create_lots', readonly=True)
    picking_type_use_existing_lots = fields.Boolean(related='move_id.picking_type_id.use_existing_lots',
                                                    readonly=True)
    def apply_lot_ids_string(self):
        self.create_move_lots_from_list(self.lot_ids_string)
        self.lot_ids_string = ""

    def create_move_lots_from_list(
        self, lot_names, virtual_tracking=True, compute_qties=True, assign_sml=False
    ):
        def check_list(lst):
            len0 = len(lst[0])
            if any(len(x) != len0 for x in lst):
                raise ValidationError(_("All serials must have same lenght"))

        def normalize_str():
            _logger.info("---->Normalizando cadena %s" % lot_names)
            lot_names.replace(".", "\n").replace(",", "\n").replace("\n", " ").split(
                " "
            )
            _logger.info("---->Normalizada a %s" % lot_names)

        if type(lot_names) is str:
            lot_names = lot_names.replace(".", "\n").replace(",", "\n").split("\n")
        if not (type(lot_names) is list):
            raise ValidationError(_("Values in unknown format"))

        values = []
        domain = [
            ("product_id", "=", self.move_id.product_id.id),
            ("name", "in", lot_names),
            ("virtual_tracking", "=", True),
        ]
        available_serial = self.env["stock.production.lot"].search_read(
            domain, ["id", "name"]
        )
        available_ids = []
        for lot in available_serial:
            lot_names.remove(lot["name"])
            available_ids.append(lot["id"])
        self.lot_ids = self.env["stock.production.lot"].browse(available_ids)
        for lot_name in lot_names:
            if not lot_name:
                continue
            values.append(
                (
                    0,
                    0,
                    {
                        "product_id": self.product_id.id,
                        "name": lot_name,
                        "virtual_tracking": virtual_tracking,
                    },
                )
            )
        self.write({"lot_ids": values})
        if compute_qties:
            self.move_id.compute_new_move_line_quantities()

    @api.onchange("lot_ids")
    def onchange_lot_ids(self):
        if self.state in ["done", "cancel", "draft"]:
            raise ValidationError(_("Incorrect move state"))

        if self.virtual_tracking and not self._context.get(
            "by_pass_compute_qties", False
        ):
            self.qty_done = len(self.lot_ids)

    @api.multi
    def action_alternative_product(self):
        self.ensure_one()
        view = self.env.ref("alternative_tracking.stock_move_line_tracking_form")
        return {
            "name": _("Tracking Form Operations"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.move.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
        }

    @api.multi
    def action_open_tracking_form(self):
        self.ensure_one()
        view = self.env.ref("alternative_tracking.stock_move_line_tracking_form")
        return {
            "name": _("Tracking Form Operations"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.move.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
        }

    def check_mrp_lot_ids(self):

        bom_lot_ids = self.lot_ids.filtered(lambda x: x.product_id != self.product_id)
        # line_lot_ids = self.lot_ids.filtered(lambda x: x.product_id == self.product_id)
        move_lot_ids = self.env["stock.production.lot"]

        product_id = bom_lot_ids.mapped("product_id")
        sql = (
            "select sml.id as id, sml.qty_done - (select count(*) from lot_id_move_line_id_rel "
            "where move_line_id = sml.id) as free_qty "
            "from stock_move_line sml "
            "join stock_move sm on sm.id = sml.move_id where "
            "sml.state = 'done' and sm.product_id = %s and not sml.production_id isnull order by sml.id asc"
        )
        sql = "select t1.id, t1.free_qty from ({}) as t1 where t1.free_qty > 0".format(
            sql
        )
        self._cr.execute(sql, [product_id.id])
        res_lines = self._cr.fetchall()
        lots_to_assign = bom_lot_ids.ids
        insert_vals = []
        free_qty = sum(x[1] for x in res_lines)
        if len(lots_to_assign) > free_qty:
            raise ValidationError(_("Too much lots to assign. Check productions"))
        lot_to_move_to_production = []
        for line in res_lines:
            for _qty in range(0, int(line[1])):
                if lots_to_assign:
                    insert_vals.append((line[0], lots_to_assign[0]))
                    lot_to_move_to_production += [lots_to_assign[0]]
                    lots_to_assign.remove(lots_to_assign[0])

        if not insert_vals:
            raise ValidationError(
                _("Not free production to assign serial. Check productions")
            )
        if lot_to_move_to_production:
            location_dest_id = self.picking_type_id.warehouse_id.pbm_loc_id.id
            sql = "update stock_production_lot set location_id=%s where id in %s"
            _logger.info(sql % (location_dest_id, tuple(lot_to_move_to_production)))
            self._cr.execute(
                sql,
                (
                    location_dest_id,
                    tuple(lot_to_move_to_production),
                ),
            )

        insert_sql = "insert into lot_id_move_line_id_rel values {}".format(
            ", ".join(["%s"] * len(insert_vals))
        )
        self._cr.execute(insert_sql, tuple(insert_vals))

        ## Creamos los nuevos lotes.
        lot_names = bom_lot_ids.mapped("name")
        self.lot_ids = move_lot_ids
        self.create_move_lots_from_list(lot_names, compute_qties=False)

        sql = (
            "select sml.id as id, sml.qty_done - (select count( *) from lot_id_move_line_id_rel "
            "where move_line_id = sml.id) as free_qty "
            "from stock_move_line sml "
            "join stock_move sm on sm.id = sml.move_id where "
            "sml.state = 'done' and sm.product_id = %s and not sm.production_id isnull order by id asc"
        )
        sql = "select t1.id, t1.free_qty from ({}) as t1 where t1.free_qty > 0".format(
            sql
        )
        self._cr.execute(sql, [self.product_id.id])
        res_lines = self._cr.fetchall()
        lots_to_assign = self.lot_ids.ids
        free_qty = sum(x[1] for x in res_lines)
        if len(lots_to_assign) > free_qty:
            raise ValidationError(_("Too much lots to assign. Check productions"))
        insert_vals = []
        for line in res_lines:
            for _qty in range(0, int(line[1])):
                if lots_to_assign:
                    insert_vals.append((line[0], lots_to_assign[0]))
                    lots_to_assign.remove(lots_to_assign[0])
        insert_sql = "insert into lot_id_move_line_id_rel values {}".format(
            ", ".join(["%s"] * len(insert_vals))
        )
        self._cr.execute(insert_sql, tuple(insert_vals))

        return


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_available_serial_ids(self):
        self.ensure_one()
        self.available_serial_ids = self.move_line_ids.mapped("available_serial_ids")

    @api.multi
    def _compute_lot_ids(self):
        for move in self:
            move.lot_ids = move.move_line_ids.mapped("lot_ids")

    lot_ids = fields.One2many(
        comodel_name="stock.production.lot",
        compute="_compute_lot_ids",
        inverse="_set_lot_ids",
    )
    available_serial_ids = fields.One2many(
        "stock.production.lot", compute=_get_available_serial_ids
    )
    # lot_name_ids = fields.Many2many(comodel_name='move.lot.name',
    #                                relation='lot_name_move_rel',
    #                                column1='move_id',
    #                                column2='lot_name_id',
    #                                string='Lot name',
    #                                domain=_get_domain_for_lots,
    #                                copy=False)
    
    virtual_tracking = fields.Boolean(related='product_id.virtual_tracking', store=True)
    #virtual_tracking = fields.Boolean(default=False)

    lot_ids_string = fields.Text("Serial list to add")
    track_from_line = fields.Boolean(
        string="Track from move line", compute="_compute_track_from_product")
    use_existing_lots = fields.Boolean(
        related="picking_id.picking_type_id.use_existing_lots", readonly=True
    )
    removal_priority = fields.Integer(string="Removal priority")
    removal_dest_priority = fields.Integer(string="Removal dest priority")
    hide_apply_button = fields.Boolean(compute="compute_show_apply_button")

    def compute_show_apply_button(self):
        if not self.product_id.virtual_tracking or self.use_existing_lots or self.state not in [('assigned', 'partially_available')]:
            self.hide_apply_button = True

    ##@api.depends("product_id", "move_line_ids")
    @api.multi
    def _compute_track_from_product(self):
        for move in self:
            product_id = move.product_id
            # move.virtual_tracking = product_id.virtual_tracking
            if move.virtual_tracking:
                _logger.info(
                    "Compute _compute_track_from_product {}: {}/ [{}]".format(
                        product_id.display_name,
                        product_id.tracking,
                        len(move.move_line_ids),
                    )
                )
                if product_id.tracking == "none":
                    move.track_from_line = len(move.move_line_ids) > 1
                elif product_id.tracking != "none":
                    move.track_from_line = (
                        len(move.move_line_ids.mapped("location_id")) > 1
                        or len(move.move_line_ids.mapped("location_dest_id")) > 1
                    )
                    _logger.info(
                        "{} and {} : {}".format(
                            len(move.move_line_ids.mapped("location_id")) > 1,
                            len(move.move_line_ids.mapped("location_dest_id")) > 1,
                            move.track_from_line,
                        )
                    )

    def apply_lot_ids_string(self):
        self.create_move_lots_from_list(self.lot_ids_string)
        self.lot_ids_string = ""

    def compute_new_move_line_quantities(self):
        for sml in self.move_line_ids:
            sml.qty_done = len(sml.lot_ids)
        return

    def _set_lot_ids(self):
        if not self.track_from_line:
            self.move_line_ids[0].lot_ids = self.lot_ids

    @api.onchange("lot_ids")
    def onchange_lot_ids(self):
        if self.track_from_line:
            raise ValidationError(_("Incorrect state. Change in move lines"))
        if self.state in ["done", "cancel", "draft"]:
            raise ValidationError(_("Incorrect move state"))
        # import pdb; pdb.set_trace()
        self.move_line_ids.lot_ids = self.lot_ids
        self.compute_new_move_line_quantities()

    def create_move_lots_from_list(
        self, lot_names, virtual_tracking=True, compute_qties=True, assign_sml=False
    ):
        self.ensure_one()
        if self.track_from_line:
            raise ValidationError(_("Incorrect state. Change in move lines"))
        return self.move_line_ids.create_move_lots_from_list(
            lot_names=lot_names,
            virtual_tracking=virtual_tracking,
            compute_qties=compute_qties,
            assign_sml=assign_sml,
        )

    def action_alternative_product(self):
        """Returns an action that will open a form view (in a popup) allowing to
        add lot for alternative tracking.
        """

        
        self.ensure_one()
        res_id = self.move_line_ids[0].id
        view = self.env.ref("alternative_tracking.stock_move_line_tracking_form")
        return {
            "name": _("Detailed Lots"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.move.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": res_id,
            "context": dict(
                self.env.context,
                default_product_id=self.product_id,
                default_usage=self.location_dest_id.usage,
            ),
        }

    def _run_valuation(self, quantity=None):
        if not self.quantity_done:
            return 0
        return super()._run_valuation(quantity=quantity)

    def filter_affected_moves(self):
        return self.filtered(
            lambda x: not x.inventory_id
            and not x.picking_type_id.bypass_tracking
            and not (x.raw_material_production_id or x.production_id)
        )
    def _action_done(self):
        virtual_tracking = self.filtered(
            lambda x: x.virtual_tracking
        ).filter_affected_moves()
        for move in virtual_tracking:
            if not len(move.lot_ids):
                raise ValidationError(_("You must enter serial names"))
        moves = super()._action_done()
        for move in virtual_tracking.filtered(lambda x: x.state == "done"):
            _logger.info("Actualizado el movimiento %s" % move.display_name)
            for sml_id in virtual_tracking.mapped("move_line_ids"):
                if sml_id.lot_ids.filtered(lambda x: x.product_id != sml_id.product_id):
                    sml_id.check_mrp_lot_ids()
        for move in self.filtered(lambda x: x.lot_ids):
            move.lot_ids.write({"location_id": move.location_dest_id.id})
        return moves
