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
    'name': 'Accounting by line of business',
    'version': '0.1',
    'category': 'Tools',
    'description': """
        Permite meter en contexto una linea de negocio para filtrar los saldos de contabilidad

        update account_account set require_business_line = true where code like '7%' and type != 'view';
        update account_account set require_business_line = true where code like '6%' and type != 'view';
        """,
    'author': 'Pexego Sistemas Informáticos',
    'website': 'https://www.pexego.es',
    'depends': ['base', 'account', 'account_financial_report_webkit', 'account_voucher', 'account_analytic_plans'],
    'init_xml': [],
    'data': ['account_move_line_view.xml',
                    'wizard/wizard_account_balance_report_view.xml',
                    'account_view.xml',
                    'account_invoice_view.xml',
                    'business_line_view.xml',
                    'account_voucher_view.xml',
                    'security/ir.model.access.csv'],
    'demo_xml': [],
    'installable': True,
    'certificate': '',
}
