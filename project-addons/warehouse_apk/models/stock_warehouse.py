from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
        ## Si a esta función le llega lot_ids:
        if not lot_id and self._context.get('force_lot_ids', False):
            lot_ids = self._context['force_lot_ids']
            lot_domain = [('lot_id', 'in', lot_ids.ids)]
            removal_strategy = self._get_removal_strategy(product_id, location_id)
            removal_strategy_order = self._get_removal_strategy_order(removal_strategy)
            domain = [
                ('product_id', '=', product_id.id),
            ]
            if not strict:
                if lot_id:
                    domain = expression.AND([lot_domain, domain])
                if package_id:
                    domain = expression.AND([[('package_id', '=', package_id.id)], domain])
                if owner_id:
                    domain = expression.AND([[('owner_id', '=', owner_id.id)], domain])
                domain = expression.AND([[('location_id', 'child_of', location_id.id)], domain])
            else:
                domain = expression.AND([lot_domain, domain])
                domain = expression.AND([[('package_id', '=', package_id and package_id.id or False)], domain])
                domain = expression.AND([[('owner_id', '=', owner_id and owner_id.id or False)], domain])
                domain = expression.AND([[('location_id', '=', location_id.id)], domain])

            # Copy code of _search for special NULLS FIRST/LAST order
            self.sudo(self._uid).check_access_rights('read')
            query = self._where_calc(domain)
            self._apply_ir_rules(query, 'read')
            from_clause, where_clause, where_clause_params = query.get_sql()
            where_str = where_clause and (" WHERE %s" % where_clause) or ''
            query_str = 'SELECT "%s".id FROM ' % self._table + from_clause + where_str + " ORDER BY "+ removal_strategy_order
            self._cr.execute(query_str, where_clause_params)
            res = self._cr.fetchall()
            # No uniquify list necessary as auto_join is not applied anyways...
            return self.browse([x[0] for x in res])

        return super()._gather(product_id=product_id, location_id=location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    @api.model
    def get_warehouse_info(self):
        return [self.env.user.actual_warehouse_id.get_info()]

    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'lot_stock_id': self.lot_stock_id.get_info()
            }
        if type > 1:
            val.update({
                
            })
        if type > 2:
            val.update ({
            
            })
        _logger.info(val)
        return val
