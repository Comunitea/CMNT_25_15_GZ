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

from odoo import models, fields, api, _

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        
        if product_id.purchase_requisition != 'tenders':
            return super(ProcurementRule, self)._run_buy(product_id, product_qty, product_uom, location_id, name, origin, values)
        group_id = values.get('group_id', False)
        if product_id.purchase_requisition == 'tenders' and group_id:
            domain = [('group_id', '=', group_id.id), ('state', 'in', ['draft', 'in_progress'])]
            pr = self.env['purchase.requisition'].search(domain, limit=1)
            if pr:
                req_line = pr.line_ids.filtered(lambda x: x.product_id == product_id) 
                if req_line:
                    req_line.product_qty += product_qty
                else:
                    new_linevalues = pr._prepare_tender_line_values(product_id, product_qty, product_uom, values)
                    pr.line_ids.create(new_linevalues)
                return True
        values = self.env['purchase.requisition']._prepare_tender_values(product_id, product_qty, product_uom, location_id, name, origin, values)
        values['picking_type_id'] = self.picking_type_id.id
        pr = self.env['purchase.requisition'].create(values)
        if group_id.sale_id:
            message = "This sale order has created this purchase requisition: <a href=# data-oe-model=purchase.requisition data-oe-id=%d>%s</a>"%(pr.id, pr.name)
            group_id.sale_id.message_post(body=message)
        return True
