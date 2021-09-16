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
    'name': 'Procurement Group Extended',
    'version': '11.0.0.0.1',
    'category': 'general',
    'description': """
        Extensión de funcionalidad para Procurement Group
        
    """,
    'author': 'Comunitea',
    'website': 'https://www.comunitea.com',
    'depends': [
        'stock', 
        'purchase', 
        'sale_stock', 
        'purchase_requisition_extended'],
    'data': [
        'views/procurement_views.xml',
        'views/stock_picking_type.xml',
        'views/stock_picking.xml',
        'views/sale_view.xml',
        'wizard/generate_copy_sale.xml',


    ],
    'installable': True,
}
