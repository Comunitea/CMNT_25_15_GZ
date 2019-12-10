##############################################################################
#
#    Copyright (C) 2004-2011 Comunitea Servicios Tecnológicos S.L.
#    All Rights Reserved
#    $Javier Colmenero Fernández$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api


class StockPackagingType(models.Model):
    _name = "stock.packaging.type"
    _description = "Packaging"

    name = fields.Char('Name', required=True,
                       help="Name of the packaging type")
    alias = fields.Char('Alias', size=3,
                        help=" Abbreviation name of the packaging type")


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    @api.model
    def checksum(self, sscc):
        """Devuelve el sscc pasado mas un dígito calculado"""
        iSum = 0
        for i in xrange(len(sscc) - 1, -1, -2):
            iSum += int(sscc[i])
        iSum *= 3
        for i in xrange(len(sscc) - 2, -1, -2):
            iSum += int(sscc[i])

        iCheckSum = (10 - (iSum % 10)) % 10

        return "{}{}".format(sscc, iCheckSum)

    @api.model
    def make_sscc(self):
        """Método con el que se calcula el sscc a partir del 1+ aecoc +
        una sequencia de 9 caracteres + 1 digito checksum
        para escribir en el name del paquete"""
        sequence = self.env['ir.sequence'].\
            next_by_code('scc.tracking.sequence')
        aecoc = self.env.user.company_id.aecoc_code
        try:
            return self.checksum("1" + aecoc + sequence)
        except Exception:
            pass

    packaging_type_id = fields.Many2one('stock.packaging.type',
                                        'Packaging Type')
    name = fields.Char(default=make_sscc)


class ResCompany(models.Model):
    _inherit = "res.company"

    aecoc_code = fields.Char('AECOC Code', size=8)
