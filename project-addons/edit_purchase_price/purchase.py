# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp import models, fields


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

#    order_line = fields.One2many(states={'done': [('readonly', True)]})


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    name = fields.Text(readonly=True, states={'draft': [('readonly', False)]})
    product_qty = fields.Float(readonly=True,
                               states={'draft': [('readonly', False)]})
    date_planned = fields.Date(readonly=True,
                               states={'draft': [('readonly', False)]})
    product_uom = fields.Many2one(readonly=True,
                                  states={'draft': [('readonly', False)]})
    product_id = fields.Many2one(readonly=True,
                                 states={'draft': [('readonly', False)]})
