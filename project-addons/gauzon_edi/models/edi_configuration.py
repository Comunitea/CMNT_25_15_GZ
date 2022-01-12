# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EdiConfiguration(models.Model):
    _name = "edi.configuration"
    _description = "Configuracion EDI"

    name = fields.Char("Nombre", required=True)
    salesman = fields.Many2one(
        "res.users",
        "Comercial para los pedidos.",
        help="Seleccione el comercial que será asignado" " a todos los pedidos.",
    )
    ftp_host = fields.Char("Host")
    ftp_port = fields.Char("Puerto", size=6)
    ftp_user = fields.Char("Usuario")
    ftp_password = fields.Char("Password")
    local_mode = fields.Boolean(
        "Modo local",
        default=True,
        help="Si es activado, el módulo no realizará "
        "conexiones al ftp. Solo trabajará con "
        "los ficheros y documentos pendientes "
        "de importación",
    )
    ftpbox_path = fields.Char("Ruta ftpbox", required=True)

    @api.model
    def get_configuration(self):
        ids = self.search([])
        if not ids:
            raise UserError(_("No hay una configuracion EDI. "))
        else:
            return ids[0]
