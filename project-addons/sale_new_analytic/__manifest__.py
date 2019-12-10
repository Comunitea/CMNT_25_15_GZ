##############################################################################
#
#    Copyright (C) 2004-TODAY
#        Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
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
{
    'name': 'New analytic account on sale',
    'version': '11.0.0.0.1',
    'category': 'Sales',
    'description': """
       Genera una nueva cuenta analítica por cada venta confirmada
    """,
    'author': 'Comunitea',
    'website': 'https://www.comunitea.com',
    'depends': ['analytic', 'sale_stock', 'sale_order_revision'],
    'data': ["views/warehouse_view.xml"],
    'installable': True,
}
