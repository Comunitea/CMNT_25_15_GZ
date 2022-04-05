##############################################################################
#
#    Copyright (C) 2004-TODAY
#        Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#        $Kiko Sánchez$
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
    'name': 'Show pending qty to invoice in SO and PO',
    'version': '11.0.0.0.1',
    'category': 'Account',
    'description': """
       Muestra la cantidad pendiente de facturar en los pedidos de venta y compra
    """,
    'author': 'Comunitea',
    'website': 'https://www.comunitea.com',
    'depends': ['account', 'sale_stock'],
    'data': [
        "views/sale_view.xml",
        "views/purchase_view.xml"
        ],
    'installable': True,
}
