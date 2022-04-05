from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)



class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
            'zip': self.zip,
            }
        if type > 1:
            val.update({
                'picking_warm_msg': self.picking_warm_msg,
                'user_id': self.user_id.get_info()
            })
        if type > 2:
            val.update ({

            })
        return val
        