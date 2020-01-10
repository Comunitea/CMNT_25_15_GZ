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

from odoo import models, fields


class AccountPaymentMode(models.Model):

    _inherit = "account.payment.mode"

    no_print = fields.Boolean("Not print")


class ResCompany(models.Model):

    _inherit = "res.company"

    lopd_text = fields.Text("LOPD Text")
