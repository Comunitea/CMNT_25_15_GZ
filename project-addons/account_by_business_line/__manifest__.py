##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Omar Castiñeira Saavedra$
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
    'name': 'Accounting by line of business',
    'version': '11.0.0.0.1',
    'category': 'Tools',
    'description': """
        Permite filtrar la contabilidad por linea de negocio

        update account_account set require_business_line = true where code like '7%' and type != 'view';
        update account_account set require_business_line = true where code like '6%' and type != 'view';
        """,
    'author': 'Comunitea Servicios Tecnológicos',
    'website': 'https://www.comunitea.com',
    'depends': ['analytic_tag_dimension', 'sale_stock', 'stock_account',
                'mrp'],
    'data': ['views/account_view.xml',
             'views/account_invoice_view.xml',
             'views/assets_backend.xml',
             'views/product.xml',
             'views/stock_view.xml',
             'views/sale_view.xml',
             'data/account_by_business_line_data.xml'],
    'qweb': ['static/src/xml/account_reconciliation.xml'],
    'installable': True,
}
