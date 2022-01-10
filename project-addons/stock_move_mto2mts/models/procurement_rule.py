##############################################################################
#
#    Copyright (C) 2020-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Kiko Sánchez$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    @api.constrains('action', 'mts_rule_id', 'mto_rule_id')
    def _check_mts_mto_rule(self):
        for rule in self:
            if rule.action == 'split_procurement':
                if not rule.mts_rule_id or not rule.mto_rule_id:
                    msg = _('No MTS or MTO rule configured on procurement '
                            'rule: %s!') % (rule.name, )
                    raise UserError(msg)
                if False and (rule.mts_rule_id.location_src_id.id !=
                        rule.mto_rule_id.location_src_id.id):
                    msg = _('Inconsistency between the source locations of '
                            'the mts and mto rules linked to the procurement '
                            'rule: %s! It should be the same.') % (rule.name,)
                    raise UserError(msg)
