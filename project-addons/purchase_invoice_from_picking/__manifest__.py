# © 2019 Numigi (tm) and all its contributors (https://bit.ly/numigiens)
# © 2020 Comunitea Servicios Tecnológicos S.L. (https://comunitea.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Purchase Invoice From Picking",
    'summary': "Create supplier bill from a receipt order",
    'author': "Numigi",
    'maintainer': "Numigi",
    'website': "https://bit.ly/numigi-com",
    'licence': "AGPL-3",
    'version': '11.0.0.0.0',
    'depends': ['purchase', 'purchase_stock_picking_invoice_link'],
    'data': [
        "views/account_invoice.xml",
        "views/stock_picking.xml",
    ],
    'installable': True,
}
