# -*- coding: utf-8 -*-
{
    'name': 'No-pickings edi',
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
    'depends': ['no_pickings', 'gauzon_edi'],
    'init_xml': [],
    'data': [],
    'demo_xml': [],
    'installable': True,
    'certificate': '',
}
