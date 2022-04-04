from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)



class StockProductPutawatStartegy(models.Model):
    _inherit = 'stock.product.putaway.strategy'

    @api.model
    def new_one(self, values):
        product_id = self.env['product.product'].browse(values.get('product_id'))
        location_id = self.env['stock.location'].browse(values.get('location_id'))
        return self._new_one(product_id, location_id)        

    def _new_one(self, product_id, location_id):
        ### Busco la primera product.putaway que haya
        parent_location_id = location_id
        putaway_id = parent_location_id.putaway_strategy_id.filtered(lambda x: x.method == 'per_product')
        while parent_location_id and not putaway_id:
            parent_location_id = parent_location_id.location_id
            putaway_id = parent_location_id.putaway_strategy_id.filtered(lambda x: x.method == 'per_product')

        if putaway_id:
            domain = [
                ('putaway_id', '=', putaway_id.id), 
                ('product_tmpl_id', '=', product_id.product_tmpl_id.id)]
            product_strat_id = self.search(domain)
            if product_strat_id:
                for ps_id in product_strat_id.filtered(lambda x: x.fixed_location_id != location_id):
                    ps_id.sequence += 1
                one = product_strat_id.filtered(lambda x: x.fixed_location_id == location_id)
                if one:
                    one.sequence = 0

            if not product_strat_id or not one:
                    vals = {
                        'sequence': 0,
                        'putaway_id':  putaway_id.id,
                        'fixed_location_id': location_id.id,
                        'product_tmpl_id': product_id.product_tmpl_id.id
                    }
                    new_one_id = self.create(vals)


        

