# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class EdiDoc(models.Model):
    _name = "edi.doc"
    _description = "Documento EDI"

    name = fields.Char("Referencia", required=True)
    file_name = fields.Char("Nombre fichero", size=64)
    type = fields.Selection(
        [
            ("orders", "Pedido"),
            ("ordrsp", "Respuesta Pedido"),
            ("desadv", "Albarán"),
            ("recadv", "Confirmación mercancia"),
            ("invoic", "Factura"),
        ],
        "Tipo de documento",
        index=1,
    )
    date = fields.Datetime("Descargado el")
    date_process = fields.Datetime("Procesado el")
    status = fields.Selection(
        [
            ("draft", "Sin procesar"),
            ("imported", "Importado"),
            ("export", "Exportado"),
            ("error", "Con incidencias"),
        ],
        "Estado",
        index=1,
    )
    mode = fields.Selection(
        [
            ("ORI", "ORI"),
            ("DEL", "DEL"),
            ("REP", "REP"),
            ("1", "Aceptado"),
            ("2", "No Aceptado"),
            ("3", "Cambiado"),
            ("9", "Original"),
            ("7", "Duplicado"),
            ("31", "Copia"),
            ("5", "Remplazo"),
        ],
        "Modo",
        readonly=True,
        index=1,
    )
    sale_order_id = fields.Many2one("sale.order", "Pedido", ondelete="restrict")
    picking_id = fields.Many2one("stock.picking", "Albaran", ondelete="restrict")
    invoice_id = fields.Many2one("account.invoice", "Factura", ondelete="restrict")
    response_document_id = fields.Many2one("edi.doc", "Documento de respuesta")
    send_response = fields.Char("Respuesta", index=1)
    send_date = fields.Datetime("Fecha del ultimo envio", index=1)
    message = fields.Text("Mensaje")
    gln_e = fields.Char("GLN Emisor", size=60, help="GLN del emisor del documento")
    gln_v = fields.Char("GLN vendedor", size=60, help="GLN del receptor del documento")
    gln_c = fields.Char("GLN comprador", size=60, help="GLN de la dirección de factura")
    gln_r = fields.Char("GLN receptor", size=60, help="GLN de la dirección de envio")

    _order = "date desc"
