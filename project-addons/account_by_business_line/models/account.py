##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Omar Castiñeira Saavedra$
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

from odoo import _, models, fields, exceptions, api


class AccountAccount(models.Model):

    _inherit = "account.account"

    require_business_line = fields.Boolean('Require business line')
    need_business_line = fields.Boolean('Need business line')


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    @api.constrains('analytic_tag_ids', 'account_id')
    def _check_if_need_business_line(self):
        for line in self:
            if line.account_id.require_business_line and \
                    not line.analytic_tag_ids.filtered('is_business_line'):
                return exceptions.\
                    ValidationError(_('This account move line needs a business'
                                      ' line to create.'))


class AccountAnalyticTag(models.Model):

    _inherit = "account.analytic.tag"

    is_business_line = fields.Boolean("Is business line")
