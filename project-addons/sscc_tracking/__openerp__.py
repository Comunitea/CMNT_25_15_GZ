# -*- coding: utf-8 -*-
{
    'name': 'sscc Stock Tracking',
    'version': '0.1',
    'category': 'Tools',
    'description': """
        Este módulo añade el campo tipo de embalaje a stock tracking y permite un correcto etiquetado de los paquetes
        mediante el sscc. Calcula las sequencias de stock.tracking de la siguiente manera:
        1+Código aeoc de la compañia(7 caracteres)+sequencia de 9 caracteres rellenada con 0 a la izquiersa y con subida unitaria + checksum.

    """,
    'author': 'Pexego',
    'website': 'https://www.pexego.es',
    'depends': ['base','stock','product'],
    'init_xml': [],
    'data': [
        'sscc_tracking_view.xml',
        'sscc_sequence.xml',
        'security/ir.model.access.csv'
    ],
    'demo_xml': [],
    'installable': True,
    'certificate': '',
}
