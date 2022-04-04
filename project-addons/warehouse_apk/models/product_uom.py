from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class UomUom(models.Model):
    _inherit = 'product.uom'

    ## wh_code = fields.Char('Warehouse Code')
    ## Utilizo el campo de edi para Gauzon
    ## wh_code = fields.Char(related="edi_code")


    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
            'wh_code': self.edi_code
            }
        return val
