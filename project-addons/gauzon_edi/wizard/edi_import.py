##############################################################################
#
#    Copyright (C) 2004-TODAY
#        Pexego Sistemas Informáticos (http://www.pexego.es) All Rights Reserved
#        $Javier Colmenero Fernández$
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

import os
import time

from lxml import etree
from odoo import _, api, exceptions, fields, models

from .edi_logging import logger

log = logger("import_edi")


class EdiImport(models.TransientModel):

    _name = "edi.import"

    configuration = fields.Many2one("edi.configuration", "Configuración", required=True)
    downloaded_files = fields.Integer("Archivos Descargados", readonly=True)
    pending_process = fields.Integer("Ficheros pendientes de procesar", readonly=True)
    state = fields.Selection(
        [
            ("start", "Empezar"),
            ("to_process", "A procesar"),
            ("processed", "Procesado"),
        ],
        "Estado",
        readonly=True,
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        conf = self.env["edi.configuration"].search([], limit=1)
        if not conf:
            raise exceptions.UserError(_("No existen configuraciones EDI."))

        res.update(
            {
                "configuration": conf.id,
                "downloaded_files": 0,
                "state": "start",
                "pending_process": 0,
            }
        )
        return res

    def get_files(self):
        """Este método es llamado cuando pulsamos el botón de obtener ficheros del asistente de importación.
        Lee los ficheros en el directorio asignado, y si no se han creado documentos para ellos,los
        crea en estado de borrador"""
        self.ensure_one()
        files_downloaded = 0
        path = self.configuration.ftpbox_path + "/in"

        if self.configuration.local_mode:
            log.info("Importando documentos en modo local")
            for file_name in os.listdir(path):
                doc_type, name = file_name.replace(".xml", "").split("_")
                if not self.env["edi.doc"].search([("name", "=", name)]):
                    f = open(path + "/" + file_name)
                    file_id = self.env["edi.doc"].create(
                        {
                            "name": name,
                            "file_name": file_name,
                            "status": "draft",
                            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "type": doc_type.lower(),
                            "message": f.read(),
                        },
                    )
                    f.close()
                    files_downloaded += 1
                    log.info("Importado %s " % name)
                    print(("Importado {} ".format(name)))
                else:
                    print("Ignorado")
                    log.info("Ignorado %s, ya existe en el sistema." % name)

            doc_ids = self.env["edi.doc"].search([("status", "in", ["draft", "error"])])
            self.write(
                {
                    "downloaded_files": files_downloaded,
                    "pending_process": len(doc_ids),
                    "state": "to_process",
                }
            )
            log.info("%s documento(s) han sido importados." % files_downloaded)
            log.info("%s documento(s) están pendientes de procesar." % len(doc_ids))

        return {
            "type": "ir.actions.act_window",
            "res_model": "edi.import",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }

    @api.model
    def get_partner(self, gln):
        partner = self.env["res.partner"].search([("gln", "=", gln)], limit=1)
        if not partner:
            raise exceptions.UserError(_("No existen ningún cliente con gln %s." % gln))
        return partner

    @api.model
    def unor_to_partner(self, unor):
        partner = self.env["res.partner"].search([("center_code", "=", unor)], limit=1)
        if not partner:
            raise exceptions.UserError(
                _("No existen ninguna dirección con UNOR %s." % unor)
            )
        return partner

    @api.model
    def get_notes(self, obs):
        observation = ""
        for line in obs:
            if line.text:
                observation += line.text + "\n"
        return observation

    def create_order(self, cdic, root, doc):
        wizard = self.env["edi.configuration"].search([], limit=1)
        if not wizard:
            raise exceptions.UserError(_("No existen configuraciones EDI."))
        ref = (
            cdic.get("gi_cab_numped", False) is not False
            and cdic["gi_cab_numped"].text
            or False
        )
        sale_id = []
        if root.attrib["gi_cab_funcion"] in ["REP", "DEL"] and ref:
            sale_id = self.env["sale.order"].search([("client_order_ref", "=", ref)])

        if sale_id or root.attrib["gi_cab_funcion"] == "ORI":
            partner = self.get_partner(cdic["gi_cab_emisor"].text)
            invoice_dir = self.get_partner(cdic["gi_cab_comprador"].text)
            shipping_dir = self.get_partner(cdic["gi_cab_shipto"].text)
            unor_dir = self.unor_to_partner(cdic["gi_cab_unor"].text)
            values = {
                "date_order": cdic.get("gi_cab_fecha", False) is not False
                and cdic["gi_cab_fecha"].text
                or time.strftime("%Y-%m-%d"),
                # TODO: Corregir búsqueda de almacén?
                "warehouse_id": self.env["stock.warehouse"].search([], limit=1).id,
                "top_date": cdic.get("gi_cab_fechatop", False) is not False
                and cdic["gi_cab_fechatop"].text
                or False,
                "client_order_ref": ref,
                "partner_id": partner.id,
                "partner_invoice_id": invoice_dir.id,
                "partner_shipping_id": shipping_dir.id,
                "partner_unor_id": unor_dir.id,
                "pricelist_id": partner.property_product_pricelist.id,
                "fiscal_position": unor_dir.property_account_position_id.id,
                "note": cdic.get("gi_cab_obs", False)
                and self.get_notes(cdic["gi_cab_obs"])
                or "",
                "order_type": root.attrib["gi_cab_funcion"],
                "urgent": root.attrib["gi_cab_nodo"] == "224" and True or False,
                "payment_term": partner.property_payment_term_id.id,
                "payment_mode_id": partner.customer_payment_mode_id.id,
                "user_id": wizard.salesman.id,
                "num_contract": cdic.get("gi_cab_numcontr", False) is not False
                and cdic["gi_cab_numcontr"].text
                or False,
            }
            if not sale_id:
                order_id = self.env["sale.order"].create(values)
                log.info("Creada orden de venta a partir del documento %s." % doc.name)
            else:
                # TODO: buscar funcion
                self.env["sale.order"].copy_quotation(sale_id)
                last_rev_id = False
                for rev in sale_id.old_revision_ids:
                    if not last_rev_id or rev.id > last_rev_id:
                        last_rev_id = rev.id
                doc_ids = self.env["edi.doc"].search(
                    [("sale_order_id", "=", sale_id), ("id", "!=", doc.id)]
                )
                if doc_ids and last_rev_id:
                    doc_ids.write({"sale_order_id": last_rev_id})
                sale_id.write(values)
                sale_id.order_line.unlink()
                if root.attrib["gi_cab_funcion"] == "DEL":
                    # TODO: Migrar
                    # ~ wf_service = netsvc.LocalService('workflow')
                    # ~ wf_service.trg_validate(uid, 'sale.order', order_id, 'cancel', cr)
                    log.info("La venta %s ha sido cancelada." % sale_obj.name)
        else:
            doc.write(
                {
                    "status": "error",
                    "message": "La referencia de este documento no existe en el sistema",
                    "mode": root.attrib["gi_cab_funcion"],
                }
            )
            log.info(
                "Error en el documento %s. La venta a la que hace referencia no existe."
                % doc.name
            )
            order_id = False

        return order_id

    @api.model
    def get_product(self, ean13v):
        product = self.env["product.product"].search([("ean13v", "=", ean13v)], limit=1)
        if not product:
            raise exceptions.UserError(
                _("No existen ningún producto con ean13v %s." % ean13v)
            )

        return product

    @api.model
    def get_product_uom(self, uom_code):
        if not uom_code:
            raise exceptions.UserError(
                _("No se estableció unidad de medida." % uom_code)
            )
        uom = self.env["product.uom"].search([("edi_code", "=", uom_code)], limit=1)
        if not uom:
            raise exceptions.UserError(_("No existe unidad de medida %s." % uom_code))

        return uom.id

    @api.model
    def get_taxes(self, product, order):
        fiscal_position = order.fiscal_position_id
        if fiscal_position:
            taxes = fiscal_position.map_tax(product.taxes_id)
        else:
            taxes = [x.id for x in product.taxes_id]

        return taxes

    @api.model
    def create_lines(self, ldic, order):
        """ Crea las lineas del pedido de ventas"""
        for l in ldic:
            lines = dict([x.tag, x] for x in ldic[l])
            umedida = (
                lines.get("gi_lin_cantped", False) is not False
                and lines["gi_lin_cantped"].attrib["gi_lin_umedida"]
                or False
            )
            umedfac = (
                lines.get("gi_lin_cantfac", False) is not False
                and lines["gi_lin_cantfac"].attrib["gi_lin_umedfac"]
                or False
            )
            product = self.get_product(lines["gi_lin_ean13v"].text)
            values = {
                "order_id": order.id,
                "product_id": product.id,
                "name": lines.get("gi_lin_descmer", False) is not False
                and lines["gi_lin_descmer"].text
                or False,
                "product_uom_qty": lines.get("gi_lin_cantped", False) is not False
                and float(lines["gi_lin_cantped"].text)
                or 0.0,
                "product_uom": self.get_product_uom(umedida),
                "price_unit": lines.get("gi_lin_precion", False) is not False
                and float(lines["gi_lin_precion"].text)
                or 0.0,
                "tax_id": [(6, 0, self.get_taxes(product, order))],
                # 'type': product.procure_method,
                "refcli": lines.get("gi_lin_refcli", False) is not False
                and lines["gi_lin_refcli"].text
                or False,
                "refprov": lines.get("gi_lin_refprov", False) is not False
                and lines["gi_lin_refprov"].text
                or False,
            }
            self.env["sale.order.line"].create(values)

        return True

    def update_doc(self, order, mode, cdic, doc):
        values = {
            "date_process": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "imported",
            "mode": mode,
            "sale_order_id": order.id,
            "gln_e": cdic.get("gi_cab_emisor", False) is not False
            and cdic["gi_cab_emisor"].text
            or False,
            "gln_v": cdic.get("gi_cab_vendedor", False) is not False
            and cdic["gi_cab_vendedor"].text
            or False,
            "gln_c": cdic.get("gi_cab_comprador", False) is not False
            and cdic["gi_cab_comprador"].text
            or False,
            "gln_r": cdic.get("gi_cab_shipto", False) is not False
            and cdic["gi_cab_shipto"].text
            or False,
        }
        return doc.write(values)

    def parse_order_file(self, filename, doc):
        """Procesa el fichero orders, creando un pedido de venta"""

        xml = etree.parse(filename)
        root = xml.getroot()
        mode = root.attrib["gi_cab_funcion"]
        cab = root[0]
        lines = root[1]
        cdic = dict([(x.tag, x) for x in cab])
        ldic = dict([(x.tag + x.attrib["n"], x) for x in lines])

        order_id = self.create_order(cdic, root, doc)
        if order_id:
            self.create_lines(ldic, order_id)
            self.update_doc(order_id, mode, cdic, doc)
            return order_id
        return False

    def change_moves(self, gilin, sscc, id_alb, doc):
        """recibe un elemento glin, se lo recorre y comprueba si existen los productos,empaquetado,
        lote y cantidad indicads"""
        dc = dict([(x.tag, x) for x in gilin])
        package_id = False
        #
        # <gi_lin_descmer>${ ((l.move_id.procurement_id) and (l.move_id.procurement_id.sale_line_id))
        # move_id =

        sale_order_id = False
        num_ped = dc["gi_lin_numped"].text
        if num_ped:
            sale_order_id = self.env["sale.order"].search(
                [("client_order_ref", "=", num_ped)], limit=1
            )
            if not sale_order_id:
                raise exceptions.UserError(
                    _("No existe el pedido con referencia %s." % num_ped)
                )

        package_id = False
        if sscc:
            package_id = self.env["stock.quant.package"].search(
                [("name", "=", sscc)], limit=1
            )
            if not package_id:
                raise exceptions.UserError(
                    _("No existe el paquete con sscc %s." % sscc)
                )

        id_product = self.env["product.product"].search(
            [("ean13v", "=", dc["gi_lin_ean13v"].text)], limit=1
        )
        if not id_product:
            raise exceptions.UserError(
                _("No existe el producto con ean13v %s." % dc["gi_lin_ean13v"].text)
            )

        if id_alb:
            id_alb = self.env["stock.picking"].search([("name", "=", id_alb)], limit=1)
            if not id_alb:
                raise exceptions.UserError(_("No existe el albaran %s" % (id_alb)))

        num_lot = dc["gi_lin_numserie"].text or False
        id_lot = False
        if num_lot:
            id_lot = self.env["stock.production.lot"].search(
                [("name", "=", num_lot), ("product_id", "=", id_product)], limit=1
            )
            if not id_lot:
                raise exceptions.UserError(
                    _(
                        "No existe el lote con nombre %s para el producto con ean13v %s."
                        % (num_lot, dc["gi_lin_ean13v"].text)
                    )
                )

        ops_ids = self.env["stock.pack.operation"].search(
            [("result_package_id", "=", package_id), ("picking_id", "=", id_alb)],
        )
        move_links_ids = self.env["stock.move.operation.link"].search(
            [("operation_id", "in", ops_ids)]
        )
        move_links_ids = self.env["stock.move.operation.link"].browse(move_links_ids)
        move_ids = []
        for t in move_links_ids:
            move_ids.append(t.move_id.id)
        move_id = self.env["stock.move"].search(
            [
                ("picking_id", "=", id_alb),
                ("id", "in", move_ids),
                ("product_id", "=", id_product),
                # ('product_qty','=',float(dc['gi_lin_cantent'].text)),
                ("procurement_id.sale_line_id.order_id", "=", sale_order_id),
            ],
            limit=1,
        )
        if not move_id:
            raise exceptions.UserError(
                _(
                    "No se encontraron movimientos con las características requeridas.Es posible que el paquete, el lote o la cantidad estén mal asignados en el fichero"
                )
            )

        if float(dc["gi_lin_cantrec"].text) > move_id.product_qty:
            raise exceptions.UserError(
                _(
                    "No es posible que la cantidad recibida sea mayor que la cantidad entregada"
                )
            )

        new_acepted_qty = move_id.acepted_qty + float(dc["gi_lin_cantrec"].text)
        move_id.write(
            {
                "acepted_qty": new_acepted_qty,
                "note": dc.get("gi_lin_obs", False) is not False
                and self.get_notes(dc["gi_lin_obs"])
                or False,
                "rejected": dc["gi_lin_reccode"].text == "REJECTED" or False,
            }
        )
        log.info(
            "Ean13v producto -> %s : La cantidad aceptada de %s actualizada en el movimiento. "
            % (dc["gi_lin_ean13v"].text, dc["gi_lin_cantrec"].text)
        )

        return True

    def parse_recadv_file(self, filepath, doc):
        """Lee el documento recadev y se recorre las lineas para pasarlas a la función, que escribe
        el campo cantidad aceptada a los movimientos"""
        xml = etree.parse(filepath)
        root = xml.getroot()
        mode = root.attrib["gi_cab_funcion"]
        cab = root[0]
        empacs = root[1]
        gi_cab_dic = dict([(x.tag, x.text) for x in cab])
        num_alb = gi_cab_dic["gi_cab_numalb"]  # sumar el OUT/
        id_alb = self.env["stock.picking"].search([("name", "=", num_alb)], limit=1)
        if not id_alb:
            doc.write(
                {
                    "status": "error",
                    "message": "La referencia de este documento no existe en el sistema",
                }
            )
            log.info(
                "Error en el documento %s. El albarán %s al que se hace referencia no existe."
                % (doc.name, num_alb)
            )

        gi_empac_dic = dict([(x.tag + x.attrib["n"], x) for x in empacs])
        for e in gi_empac_dic:
            sscc = gi_empac_dic[e].attrib["gi_empaq_sscc"]
            for gl in gi_empac_dic[e]:
                for gilin in gl:
                    self.change_moves(gilin, sscc, num_alb, doc)

        f = open(filepath)
        doc.write(
            {
                "status": "imported",
                "date_process": time.strftime("%Y-%m-%d %H:%M:%S"),
                "mode": mode,
                "sale_order_id": False,
                "picking_id": id_alb,
                "gln_e": gi_cab_dic.get("gi_cab_emisor", False)
                and gi_cab_dic["gi_cab_emisor"]
                or False,
                "gln_v": gi_cab_dic.get("gi_cab_vendedor", False)
                and gi_cab_dic["gi_cab_vendedor"]
                or False,
                "gln_c": gi_cab_dic.get("gi_cab_comprador", False)
                and gi_cab_dic["gi_cab_comprador"]
                or False,
                "gln_r": False,
                "message": f.read(),
            }
        )
        log.info("El documento %s ha sido importado." % doc.name)
        f.close()
        return id_alb

    def process_files(self):
        """Busca todos los ficheros que estén en error o en borrador y los procesa dependiendo del
        tipo que sean"""

        path = self.configuration.ftpbox_path + "/in"
        docs = self.env["edi.doc"].search([("status", "in", ["draft", "error"])])
        model = "sale"
        act = "action_quotations"
        order_picks = []

        for doc in docs:
            file_path = path + "/" + doc.file_name
            if doc.type == "orders":
                line = self.parse_order_file(file_path, doc)
                if line:
                    order_picks.append(line)
            elif doc.type == "recadv":
                model = "stock"
                act = "action_picking_tree"
                line = self.parse_recadv_file(file_path, doc)
                order_picks.append(line)
        if order_picks:
            action = self.env.ref("{}.{}".format(model, act))
            action_data = action.read()[0]
            action_data["context"] = {}
            action_data["domain"] = [("id", "in", order_picks.ids)]
            return action_data
        return True
