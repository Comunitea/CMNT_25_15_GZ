##############################################################################
#
#    Copyright (C) 2020-TODAY
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
{
    'name': 'Split Excess Qty',
    'version': '11.0.0.0.1',
    'category': 'stock',
    'description': """
        Si un movimiento de tipo marcado como split excess qty, y con move_dest_ids, es decir, tiene un excess_picking_type, entonces la cantidad en exceso se envía segun ese tipo
        La cantidad sobrante: la que no haga falta para los move_dest_ids.
    """,
    'author': 'Comunitea',
    'website': 'https://www.comunitea.com',
    'depends': [
        'sale_stock', 
        ],
    'data': [
        'views/stock_picking_type.xml',
    ],
    'installable': True,
}
