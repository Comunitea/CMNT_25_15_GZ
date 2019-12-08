# Copyright 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Tier Validation",
    "summary": "Extends the functionality of Sales Orders to "
               "support a tier validation process.",
    "version": "11.0.1.1.0",
    "category": "Sales",
    "website": "https://github.com/OCA/sale-workflow",
    "author": "Comunitea, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
        "base_tier_validation_extend",
    ],
    "data": [
        "views/sale_order_view.xml",
    ],
}
