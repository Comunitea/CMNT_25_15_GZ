# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import api, fields, models
from openerp.osv import fields as oldfields, osv


class hr_attendance(osv.osv):
    _inherit = "hr.attendance"

    _columns = {
        'name': oldfields.datetime('Date', required=True, select=1, track_visibility='onchange'),
    }

class HrAttendance(models.Model):
    _name = 'hr.attendance'
    _inherit = ['hr.attendance', 'mail.thread']    
    
    @api.one
    def fix_register(self):
        self.write({'state': 'right'})

    state = fields.Selection(
        selection=[('fix', 'Fix'), ('right', 'Right')],
        default='right',
        help='The user did not register an input '
        'or an output in the correct order, '
        'then the system proposed one or more regiters to fix the problem '
        'but you must review the created register due '
        'becouse of hour could be not correct' )
