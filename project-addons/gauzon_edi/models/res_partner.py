# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    gln = fields.Char(
        "GLN",
        size=80,
        help="Numero de localizacion global: esta destinado a "
        "la identificacion inequivoca y no ambigua de "
        "Locaciones fisicas, legales o funcionales",
    )
    customer_reference = fields.Char(
        "Código de referencia",
        size=80,
        help="Es el código en que le identifica en el sistema del "
        "cliente, normalmente es el id de cliente o de id de "
        "proveedor que este le asigna.",
    )
    edi_relation = fields.Selection(
        [("GC", "Gran consumo"), ("MC", "Mercancia general")], "Tipo de relacion"
    )
    edi_operational_code = fields.Char("Punto operacional")
    center_code = fields.Char(
        "Id. del centro",
        size=80,
        help="Codigo de centro, un identificador unico "
        "de este centro para el cliente. Este "
        "codigo es usado para el envio/recepcion "
        "de ficheros EDI, y la impresion de "
        "etiquetas.",
    )
