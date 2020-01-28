##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Javier Colmenero Fernández$
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
    'name': 'Gauzon Custom',
    'version': '11.0.0.0.1',
    'category': 'general',
    'description': """
        Personalizaciones para gauzón
    """,
    'author': 'Comunitea',
    'website': 'https://www.comunitea.com',
    'depends': ['product', 'sale_stock', 'account', 'analytic',
                'purchase_discount', 'sale_disable_inventory_check',
                'delivery', 'stock_picking_invoice_link',
                'account_analytic_parent'],
    'data': [
        'data/gauzon_custom_data.xml',
        'views/account_invoice_view.xml',
        'views/account_move_view.xml',
        'views/analytic_line_view.xml',
        'views/product_view.xml',
        'views/partner_view.xml',
        'views/purchase_view.xml',
        'views/stock_view.xml'
    ],
    'installable': True,
}
