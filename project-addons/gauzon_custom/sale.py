# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos. All Rights Reserved
#    $Omar Castiñeira Saavedra$
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if vals.get('state', False) == "draft":
            for sale in self:
                for line in sale.order_line:
                    line.state = "draft"

        return res
