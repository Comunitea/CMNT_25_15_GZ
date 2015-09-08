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
        Se recalculan los % albaranado y % facturado del pedido y se modifica el flujo de ventas
    """,
    'author': 'Pexego',
    'website': 'https://www.pexego.es',
    'depends': ['base','sale','stock'],
    'init_xml': [],
    'data': [
        'no_pickings_view.xml',
        'no_pickings_workflow.xml',
        'wizard/moves_to_pick_view.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'certificate': '',
}
