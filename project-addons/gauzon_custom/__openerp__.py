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
{
    'name': 'Gauzon Custom',
    'version': '0.1',
    'category': 'general',
    'description': """
        Personalizaciones para gauzón
    """,
    'author': 'Pexego Sistemas Informáticos',
    'website': 'https://www.pexego.es',
    'depends': ['base', 'product', 'sale_stock', 'account', 'purchase', 'analytic', 'purchase_discount'],
    'init_xml': [],
    'data': [
        'account_invoice_view.xml',
        'account_move_view.xml',
        'account_tax_code_view.xml',
        'analytic_line_view.xml',
        'product_view.xml',
        'partner_view.xml',
        'purchase_view.xml',
        'sale_view.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'certificate': '',
}
