# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 1.3 Thinkopen Solutions, Lda. All Rights Reserved
#    http://www.thinkopensolutions.com.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version $revnoof the License, or
#    (at your option) any later version.51
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

import time
from datetime import datetime
from openerp import _
from openerp.osv import orm, fields

class sale_validation(orm.Model):
    _name="sale.order"
    _inherit="sale.order"
    _description = "Sales Order with Validation"

    STATE_SELECTION = [('draft', 'Draft Quotation'),
                       ('wait_valid', 'Waiting for Validation'),
                       ('wait_correct', 'Waiting for Correction'),
                       ('sent', 'Quotation Sent'),
                       ('waiting_date', 'Waiting Schedule'),
                       ('manual', 'Sale to Invoice'),
                       ('progress', 'Sales Order'),
                       ('shipping_except', 'Shipping Exception'),
                       ('invoice_except', 'Invoice Exception'),
                       ('done', 'Done'),
                       ('cancel', 'Cancelled')]

    _columns = {'validation_date':fields.datetime('Validation Date', readonly=True, copy=False, help="Date on which sale order has been approved"),
                'validation_user': fields.many2one('res.users', 'Validated by', readonly=True, copy=False),
                'validation_observation': fields.text('Observations', size=128, readonly=True, copy=False),
                'state': fields.selection(STATE_SELECTION,  'Status', readonly=True, copy=False, help="Gives the status of the quotation or sales order.\
              \nThe exception status is automatically set when a cancel operation occurs \
              in the invoice validation (Invoice Exception) or in the picking list process (Shipping Exception).\nThe 'Waiting Schedule' status is set when the invoice is confirmed\
               but waiting for the scheduler to run on the order date.", select=True)}

    #TODO: implement messages system
    def wkf_wait_validation_order(self, cr, uid, ids, context=None):
        for so in self.browse(cr, uid, ids, context=context):
            if not so.order_line:
                raise orm.except_orm(_('Error !'),_('You can not wait for sale order to be validated without Sale Order Lines.'))
            message = _("Sale order '%s' is waiting for validation.") % (so.name,)
            self.log(cr, uid, so.id, message)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'wait_valid'})
        return True

    #TODO: implement messages system
    def wkf_wait_correction(self, cr, uid, ids, context=None):
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'wait_correct'})
        return True

    def wkf_validating_user_time(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'validation_date': datetime.now(),
                                  'validation_user': uid})
        return True
