{
    'name': 'sscc Stock Tracking',
    'version': '11.0.0.0.1',
    'category': 'Tools',
    'description': """
        Este módulo añade el campo tipo de embalaje a stock tracking
        y permite un correcto etiquetado de los paquetes
        mediante el sscc. Calcula las sequencias de stock.tracking
        de la siguiente manera:
        1+Código aeoc de la compañia(7 caracteres)+sequencia de
        9 caracteres rellenada con 0 a la izquiersa y con subida
        unitaria + checksum.

    """,
    'author': 'Comunitea',
    'website': 'https://www.comunitea.com',
    'depends': ['stock'],
    'data': [
        'views/sscc_tracking_view.xml',
        'data/sscc_sequence.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}
