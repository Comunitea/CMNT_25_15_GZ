# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-TODAY
#        Pexego Sistemas Informáticos (http://www.pexego.es) All Rights Reserved
#        $Javier Colmenero Fernández$
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

from openerp.osv import orm

class moves_to_pick(orm.TransientModel):
    _inherit = 'moves.to.pick'

    def default_get(self, cr, uid, fields, context=None):
        """ Heredamos del asistente de no_pickings, para que compruebe si las posiciones fiscales
        son iguales, en caso contrario lanza exepción"""
        if context is None: context = {}
        res = {}
        id_address = False
        move_ids = context.get('active_ids', [])
        if not move_ids or not context.get('active_model') == 'stock.move':
            return res

        if 'move_ids' in fields:
            move_ids = self.pool.get('stock.move').browse(cr, uid, move_ids, context=context)
            # Lanzamos una excepción si alguna dirección es diferente
            set_fp = set()
            for m in move_ids:
                if m.sale_line_id:
                    set_fp.add(m.sale_line_id.order_id.fiscal_position.id)

            if set_fp and len(set_fp) != 1: #hay mas de una posición fiscal
                raise orm.except_orm(_('Error'), _('Las posiciones fiscales de los pedidos son diferentes'))

        return super(moves_to_pick,self).default_get(cr,uid,fields,context)

