# -*- coding: utf-8 -*-
{
    'name': 'No-pickings',
    'version': '0.1',
    'category': 'Tools',
    'description': """
        Este módulo permite que no se albaranen los movimientos creados mediante la confirmación
        de un pedido de venta,si el campo no albaranar (no_picking) está marcado.
        Se añade un asistente que permite crear un abarán con varios movimientos de distintos pedidos,
        siempre y cuando los pedidos de los que proceden tengan la misma dirección de destino.
    """,
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'depends': ['base','sale_stock'],
    'data': [
        'no_pickings_view.xml',
        'wizard/moves_to_pick_view.xml'
    ],
    'installable': True,
}
