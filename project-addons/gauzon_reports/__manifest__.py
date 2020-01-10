##############################################################################
#
#    Copyright (C) 2004-2011 Comunitea Servicios Tecnológicos S.L.
#    All Rights Reserved
#    $Javier Colmenero Fernández$
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
    "name": "Gauzon - Informes",
    "version": "11.0.0.0.0",
    "author": "Comunitea",
    "website": "https://www.comunitea.com",
    "category": "Enterprise Specific Modules",
    "description": """Informes para Gauzón.""",
    "depends": ['sale_stock', 'purchase', 'account', 'account_payment_sale',
                'account_payment_purchase','purchase_discount','gauzon_edi',
                'stock_picking_report_valued', 'partner_fax',
                'account_by_business_line', 'gauzon_custom', 'delivery',
                'account_invoice_report_due_list',
                'account_invoice_report_grouped_by_picking'],
    "data": ['views/sale_view.xml',
             'views/stock_view.xml',
             'views/invoice_view.xml',
             'views/purchase_view.xml',
             'views/report_templates.xml',
             'views/sale_order_templates.xml',
             'views/purchase_order_templates.xml',
             'views/stock_picking_templates.xml',
             'views/account_invoice_templates.xml',
             'reports/gauzon_reports.xml'],
    "installable": True,
}
