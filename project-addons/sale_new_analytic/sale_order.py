# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011 Pexego Sistemas Informáticos. All Rights Reserved
#    $Santiago Argüeso Armesto$
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

class sale_order(orm.Model):

    _inherit = "sale.order"

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, context=None):
        res = super(sale_order, self).onchange_warehouse_id(cr, uid, ids,
                                                            warehouse_id,
                                                            context=context)
        if warehouse_id:
            warehouse = self.pool.get('stock.warehouse').\
                browse(cr, uid, warehouse_id, context=context)
            if warehouse.analytic_account_id:
                res['value']['project_id'] = warehouse.analytic_account_id.id
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        sale =  self.browse (cr, uid, id)
        if sale:
            default.update({
                'project_id': sale.warehouse_id.analytic_account_id and sale.warehouse_id.analytic_account_id.id or False
            })
        return super(sale_order, self).copy(cr, uid, id, default, context=context)

    def action_wait(self, cr, uid, ids, context=None):

        if super(sale_order, self).action_wait(cr, uid, ids, context=context):
            sale_obj =self.browse (cr, uid, ids, context=context)
            for sale in sale_obj:
                if sale.project_id and sale.project_id.name != sale.name and sale.project_id.name != sale.unrevisioned_name:
                    analytic_obj=self.pool.get('account.analytic.account')
                    child_ids = analytic_obj.search(cr, uid, [('parent_id', '=', sale.project_id.id),('name', '=', sale.unrevisioned_name)])
                    if not child_ids:
                        vals= {
                            'name': sale.unrevisioned_name,
                            'parent_id': sale.project_id.id,
                            'type':'normal',
                            'state':'open',
                            'date_start':sale.date_confirm,
                            'currency_id': sale.pricelist_id.currency_id.id,
                            'user_id':sale.user_id.id,
                        }
                        new_analytic_id = analytic_obj.create(cr,uid,vals)
                    else:
                        new_analytic_id = child_ids[0]
                    self.write(cr, uid, sale.id, {'project_id': new_analytic_id})
        return True
