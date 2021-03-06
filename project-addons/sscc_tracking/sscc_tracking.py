# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011 Pexego Sistemas Informáticos. All Rights Reserved
#    $Javier Colmenero Fernández$
#
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
from openerp.osv import orm, fields

class stock_packaging_type(orm.Model):
   _name = "stock.packaging.type"
   _description = "Packaging"

   _columns = {
    'name' : fields.char('Name', size=256, required=True, help="Name of the packaging type"),
    'alias' : fields.char('Alias', size=3, help=" Abbreviation name of the packaging type"),
   }


class stock_quant_package(orm.Model):

    _inherit = "stock.quant.package"

    def checksum(self,sscc):
        """Devuelve el sscc pasado mas un dígito calculado"""
        iSum = 0
        for i in xrange(len(sscc)-1,-1,-2):
            iSum += int(sscc[i])
        iSum *= 3
        for i in xrange(len(sscc)-2,-1,-2):
            iSum += int(sscc[i])

        iCheckSum = (10 - (iSum % 10)) % 10

        return "%s%s" % (sscc, iCheckSum)

    def make_sscc(self, cr, uid, context=None):
        """Método con el que se calcula el sscc a partir del 1+ aecoc + una sequencia de 9 caracteres + 1 digito checksum
        para escribir en el name del paquete"""
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'scc.tracking.sequence') #sequencia definida en sscc_sequence.tracking
        aecoc = self.pool.get('res.users').browse(cr,uid,uid).company_id.aecoc_code
        try:
            return str(self.checksum("1" + aecoc + sequence ))
        except Exception:
            return sequence

    _columns = {
        'packaging_type_id' : fields.many2one('stock.packaging.type','Packaging Type'),
    }
    _defaults = {
        'name': make_sscc,
    }


class res_company(orm.Model):
    _inherit = "res.company"

    _columns = {
        'aecoc_code' : fields.char('AECOC Code', size=8),
    }
