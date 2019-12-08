# Copyright 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Base Tier Validation Extend",
    "summary": "Extends the functionality of Base Tier addon with "
               "the comment wizard of 12.0 version.",
    "version": "11.0.1.1.0",
    "category": "Tools",
    "website": "https://github.com/OCA/server-ux",
    "author": "Comunitea, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base_tier_validation",
    ],
    "data": [
        "wizard/comment_wizard_view.xml",
        'views/tier_definition_view.xml',
        'views/tier_review_view.xml'
    ],
}
