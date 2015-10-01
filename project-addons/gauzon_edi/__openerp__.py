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
    'name': 'EDI',
    'version': '0.1',
    'category': 'Tools',
    'description': """
        Importar/Exportar archivos EDI (Ventas, Albaranes y facturas)

        Este módulo modifica los objetos:
            Empresa (res.partner), añade el campo GLN (Numero de localizacion global).
            Direccion (res.partner.address), añade el campo GLN, posición fiscal y código de centro.
            Tipo de pago (account.payment.type), añade un campo 'codigo EDI' para identificar con EDI cada tipo de pago.
            Unidades de medida (product.uom), añade un campo 'código EDI' para identificar con edi cada unidad de medida.

        Es necesario que asigne los valores correctos a los campos GLN para que el modulo funcione correctamente.

    """,
    'author': 'Pexego Sistemas Informáticos',
    'website': 'https://www.pexego.es',
    'depends': ['base', 'account', 'sale', 'account_payment', 'account_payment_sale', 'sale_order_revision', 'group_products_invoicing'],
    'init_xml': [],
    'data': [
        'security/ir.model.access.csv',
        'gauzon_edi_view.xml',
        'gauzon_edi_data.xml',
        'wizard/edi_import_view.xml',
        'wizard/edi_export_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'certificate': '',
}
