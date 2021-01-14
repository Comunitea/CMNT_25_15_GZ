##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Kiko Sánchez$
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

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ProductSProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False):
        if self._context.get('seller_id', False):
            print ("Forzado de supplier info a %s" % self._context['seller_id'].name)
            return self._context['seller_id']
        return super()._select_seller(partner_id=partner_id, quantity=quantity,date=date,uom_id=uom_id)

    @api.multi
    def _select_seller_without_qty(self, partner_id=False, quantity=0.0, date=None, uom_id=False):
        self.ensure_one()
        if date is None:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        res = self.env['product.supplierinfo']
        sellers = self.seller_ids
        if self.env.context.get('force_company'):
            sellers = sellers.filtered(
                lambda s: not s.company_id or s.company_id.id == self.env.context['force_company'])
        for seller in sellers:
            # Set quantity in UoM of seller
            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [partner_id, partner_id.parent_id]:
                continue
            if seller.product_id and seller.product_id != self:
                continue

            res |= seller
        return res