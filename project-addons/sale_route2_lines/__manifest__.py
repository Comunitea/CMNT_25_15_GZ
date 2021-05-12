##############################################################################
#
#    Copyright (C) 2004-2012 Comunitea Servicios Tecnológicos S.L.
#    All Rights Reserved
#    $Kiko Sánchez$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
    "name": "Sale Route to lines",
    "description": """
       Apply route from sale order to order lines.
        """,
    "version": "11.0.0.0.0",
    "author": "Comunitea",
    "depends": ["sale_stock"],
    "category": "Sales Management",
    "data": ["views/sale_view.xml"],
    'installable': True,
}
