# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Pexego Sistemas Informáticos (http://www.pexego.es) All Rights Reserved
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
    'name': 'Customer product name',
    'version': '0.1',
    'category': 'Purchases',
    'description': """Permite poner en productos un nombre distinto por clientes y luego lo recupera en las ventas""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'https://www.pexego.es',
    'depends': ['base', 'product', 'sale'],
    'init_xml': [],
    'data': ['product_view.xml',
                   'security/ir.model.access.csv'],
    'demo_xml': [],
    'installable': True,
    'certificate': '',
}
