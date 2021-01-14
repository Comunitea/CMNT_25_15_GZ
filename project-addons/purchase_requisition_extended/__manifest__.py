##############################################################################
#
#    Copyright (C) 2004-TODAY
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
    'name': 'Purchase Requisition Extended',
    'version': '11.0.0.0.1',
    'category': 'Purchases',
    'description': """Genera líneas de compra para cada seller, proponiendo la primera""",
    'author': 'Comunitea',
    'website': 'https://www.comunitea.com',
    'depends': ['stock', 'product', 'purchase', 'purchase_discount', 'purchase_requisition'],
    'data': ['views/purchase_views.xml',
             'views/sale_views.xml',
             'views/purchase_requisition.xml'],
    'installable': True,
}
