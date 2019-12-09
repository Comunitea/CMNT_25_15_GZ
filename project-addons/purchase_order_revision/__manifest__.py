# Copyright 2019 Akretion - Renato Lima (<http://akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Purchase Order Revisions',
    'version': "11.0.1.0.0",
    'category': "Sale Management",
    'author': "Akretion, "
              "Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
    ],
    'data': [
        'views/purchase_order.xml',
    ],
    'installable': True,
    'post_init_hook': 'populate_unrevisioned_name',
}