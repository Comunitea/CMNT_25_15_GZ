from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class SalerOrder(models.Model):
    _inherit = 'sale.order'

    ## wh_code = fields.Char('Warehouse Code')
    ## Utilizo el campo de edi para Gauzon
    ## wh_code = fields.Char(related="edi_code")


    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
            }
        return val
