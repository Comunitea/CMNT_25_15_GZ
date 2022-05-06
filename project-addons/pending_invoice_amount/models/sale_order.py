from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.addons import decimal_precision as dp



class SaleOrder(models.Model):

    _inherit = "sale.order"



class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

