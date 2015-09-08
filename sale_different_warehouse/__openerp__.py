# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2012 Pexego Sistemas Informáticos All Rights Reserved
#    $Marta Vázquez Rodríguez$ <marta@pexego.es>
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
    "name" : "Sale different warehouse",
    "description": """
       Allows you to have a warehouse for each sale line and create pickings for each different warehouse.
        """,
    "version" : "1.0",
    "author" : "Pexego",
    "depends" : ["base", "stock","sale","purchase","procurement"],
    "category" : "Sales Management",
    "init_xml" : [],
    "data" : ["sale_view.xml",
                    "stock_view.xml"
                    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
