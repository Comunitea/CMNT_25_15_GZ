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

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'
    
    requisition_id = fields.Many2one('purchase.requisition', string='Purchase Req')
    purchase_requisition = fields.Selection(
        [('rfq', 'Create a draft purchase order'),
         ('tenders', 'Propose a call for tenders')],
        string='Procurement', default='rfq')

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        group_id = values.get('group_id', False)
        if group_id.purchase_requisition == 'rfq' or product_id.purchase_requisition == 'rfq':
            return super(ProcurementRule, self)._run_buy(product_id, product_qty, product_uom, location_id, name, origin, values)
        
        if group_id:
            domain = [('group_id', '=', group_id.id), ('state', 'in', ['draft', 'in_progress'])]
            pr = self.env['purchase.requisition'].search(domain, limit=1)
            if not pr:
                tender_values = self.env['purchase.requisition']._prepare_tender_values(product_id, product_qty, product_uom, location_id, name, origin, values)
                tender_values['picking_type_id'] = self.picking_type_id.id
                tender_values['user_id'] = group_id.create_uid.id
                pr = self.env['purchase.requisition'].create(tender_values)  
                group_id.requisition_id = pr
            else:
                req_line = pr.line_ids.filtered(lambda x: x.product_id == product_id) 
                if req_line:
                    if values['move_dest_ids']:
                        req_line.write({'move_dest_ids': [(4, values['move_dest_ids'].id)]})
                    req_line.product_qty += product_qty
                else:
                    new_linevalues = pr._prepare_tender_line_values(product_id, product_qty, product_uom, values)
                    req_line = pr.line_ids.create(new_linevalues)
            
        #if group_id.sale_id:
        #    message = "This sale order has been assigned to purchase requisition: <a href=# data-oe-model=purchase.requisition data-oe-id=%d>%s</a>"%(pr.id, pr.name)
        #    group_id.sale_id.message_post(body=message)

        return True
