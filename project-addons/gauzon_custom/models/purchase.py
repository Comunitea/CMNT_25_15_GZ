##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

from odoo import api, models, fields


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    global_analytic_id = fields.\
        Many2one('account.analytic.account', 'Analytic account',
                 help="This account is entered by default for new lines")
    carrier_id = fields.Many2one("delivery.carrier", "Delivery Method")

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if not self.partner_id:
            self.carrier_id = False
        else:
            self.carrier_id = self.partner_id.property_delivery_carrier_id.id
        return res

    @api.multi
    def action_view_invoice(self):
        res = super().action_view_invoice()
        del res['context']['default_reference']
        return res

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        super()._onchange_picking_type_id()
        if self.picking_type_id.analytic_tag_id:
            self.global_analytic_id = self.picking_type_id.analytic_tag_id.id
