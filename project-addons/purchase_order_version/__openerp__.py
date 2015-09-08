# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2015 Pexego Sistemas Informáticos. All Rights Reserved
#    $Omar Castiñeira Saavedra$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
        "name" : "Purchase orders versions",
        "description": """
            Módulo que permite la creación de versiones de pedidos de compra.
            Añade a los pedidos de compra el campo activo, así como la referancia a la versión original del pedido de compra y el listado de versiones anteriores.
            Botón para realizar una nueva versión del pedido de compra, todo en la vista formulario.
            Modifica el análisis de cmpras para poder filtrar por pedidos de compra activos ( por defecto ) e inactivos.""",
        "version" : "1.0",
        "author" : "Pexego",
        "website" : "http://www.pexego.es",
        "category" : "Purchase/Version",
        "depends" : [
            'base',
            'purchase'],
        "init_xml" : [],
        "demo_xml" : [],
        "data" : ['purchase_view.xml',
                        'report/purchase_report_view.xml'],
        "installable": True,
        'active': False

}
