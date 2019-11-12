# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológivcos.
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

from openerp import models, fields

#TODO: Migrar
# ~ class ProcurementOrder(models.Model):

    # ~ _inherit = "procurement.order"

    # ~ sequence = fields.Integer('Sequence')

    # ~ def _run_move_create(self, cr, uid, procurement, context=None):
        # ~ vals = super(ProcurementOrder, self)._run_move_create(cr, uid,
                                                              # ~ procurement,
                                                              # ~ context=context)
        # ~ if procurement.sequence:
            # ~ vals['sequence'] = procurement.sequence
        # ~ return vals
