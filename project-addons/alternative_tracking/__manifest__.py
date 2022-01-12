# © 2018 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Alternative Tracking",
    "version": "11.0.0.0.0",
    "category": "Product",
    "license": "AGPL-3",
    "author": "Comunitea, ",
    "depends": [
        "mrp",
        "stock",
        "stock_account",
        "stock_move_location",
        "web_widget_color",
        # NOT BATCH PICKING
        #"stock_picking_batch_extended",
    ],
    "data": [
        # 'data/data.xml',
        "security/ir.model.access.csv",
        "views/stock_move.xml",
        "views/stock_picking.xml",
        # NOT BATCH PICKING
        #"views/stock_picking_batch.xml",
        "views/stock_production_lot.xml",
        "views/product_views.xml",
        "views/stock_inventory.xml",
        "views/move_line_grouped.xml",
        "views/stock_location.xml",
        # 'views/at_tracking_assets.xml'
        # 'wizard/stock_move_change_reserve_wzd.xml'
    ],
    "installable": True,
}
