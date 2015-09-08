# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2015 Pexego Sistemas Informáticos. All Rights Reserved
#    $Omar Castiñeira Saavedra$
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
from openerp.tools import ustr


class purchase_order(orm.Model):

    _inherit = "purchase.order"

    def _get_version_ids(self, cr, uid, ids, field_name, arg, context=None):
        if context is None: context = {}
        res = {}
        for purchase in self.browse(cr, uid, ids):
            if purchase.purchase_version_id:
                res[purchase.id] = self.search(cr, uid, ['|',('purchase_version_id','=',purchase.purchase_version_id.id), ('id','=',purchase.purchase_version_id.id), ('version','<',purchase.version), '|',('active','=',False),('active','=',True)])
            else:
                res[purchase.id] = []
        return res

    _columns = {
        'purchase_version_id': fields.many2one('purchase.order', 'Orig version', readonly=True),
        'version': fields.integer('Version no.', readonly=True),
        'active': fields.boolean('Active', help="It indicates that the purchase order is active."),
        'version_ids': fields.function(_get_version_ids, method=True, type="one2many", relation='purchase.order', string='Versions', readonly=True)
    }

    _defaults = {
        'active': True,
        'version': 0
    }

    def action_previous_version(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}

        purchase_obj = self.browse(cr, uid, id, context=context)
        purchase_ids = []
        for purchase in purchase_obj:
            vals = {}
            if not purchase.purchase_version_id:
                vals.update({'purchase_version_id':purchase.id,
                             'version': 1})
            else:
                vals.update({'version': purchase.version + 1})
            new=self.copy(cr, uid, purchase.id, vals)
            if not purchase.purchase_version_id:
                self.write(cr, uid, [new], {'name': purchase.name + u" V.1"})
            else:
                self.write(cr, uid, [new], {'name': purchase.purchase_version_id.name + u" V." + ustr(purchase.version + 1)})
            purchase.write({'active': False})
            purchase_ids.append(new)
        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'purchase', 'purchase_order_form')
        res_id = res and res[1] or False,

        return {
            'name': 'Purchase Order',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res_id,
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': purchase_ids and purchase_ids[0] or False,
        }

