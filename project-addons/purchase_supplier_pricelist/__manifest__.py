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
    'name': 'Purchase supplier pricelist',
    'version': '11.0.0.0.1',
    'category': 'Purchases',
    'description': """Permite calcular el precio de las linea de precios de
productos por bruto - descuento, también permite decidir en que divisa esta
ese precio.""",
    'author': 'Comunitea',
    'website': 'https://www.comunitea.com',
    'depends': ['product', 'purchase', 'purchase_discount'],
    'data': ['views/product_view.xml'],
    'installable': True,
}
