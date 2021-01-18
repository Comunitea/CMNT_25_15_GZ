# Copyright 2019 Comunitea - Kiko Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Product putaways in product",
    "summary": "Module to show putwawys in product, and allow create putaway from picks",
    "version": "12.0.1.0.0",
    "author": "Comunitea",
    "category": "Inventory",
    "depends": ["stock", "stock_putaway_product"],
    "data": [
        "views/product_views.xml",
        "views/models.xml",

    ],
    "installable": True,
    "license": "AGPL-3",
}
