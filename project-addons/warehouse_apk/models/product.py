from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    allow_location_to_inc = fields.Boolean('Scan loc +1', default = False, help="To avoid barcode tags in products, scan a location in a move, inc +1 in move line qty done")
    

class ProductProduct(models.Model):
    _inherit = 'product.product'


    @api.model
    def get_product_info(self, values):
        _logger.info("Contexto: %s y usuario %s" %(self._context, self.env.user))
        info_type = values.get('info_type', 0)
        id = values.get('id')
        location_id= values.get('location_id')

        stock_domain = values.get('stock_domain', [('location_id', 'child_of', location_id)])
        res = {}
        ctx = self._context.copy()
        if location_id:
            ctx.update(location=location_id)
        product_id = self.with_context(ctx).browse(id)
        res['product'] = product_id.get_info(info_type)
        if info_type > 2:
            res['stock'] = product_id.get_stock(stock_domain)
        return res
    
    def get_default_location_putaway(self):
        putaway_strategy_id = self.env.user.actual_warehouse_id.lot_stock_id.putaway_strategy_id
        if putaway_strategy_id and putaway_strategy_id.method == 'per_product':
            strategies = putaway_strategy_id.get_product_putaway_strategies(self)
            strategy = strategies[:1]
            if strategy:
                return strategy.fixed_location_id
        return self.env['stock.location']
        
    def get_stock(self, stock_domain=[]):
        domain = [('product_id', '=', self.id)]
        if stock_domain:
            domain += stock_domain
        _logger.info("Buscando stock para %s con dominio\n%s"%(self.display_name, domain))
        stock = self.env['stock.quant'].search(domain)
        res = []
        for quant in stock:
            q_vals = {
                'id': quant.id,
                'location_id': quant.location_id.get_info(),
                'lot_id': quant.lot_id and quant.lot_id.get_info() or {},
                'quantity': quant.quantity,
                'reserved_quantity': quant.reserved_quantity,
                }
            res.append(q_vals)
        print(res)
        return res

    def get_info(self, type=0):
        if not self:
            return {}
        val = {
            'id': self.id,
            'name': self.name,
            'tracking': self.tracking,
            'barcode': self.barcode,
            'refcli': self.refcli,
            'default_code': self.default_code,
            'allow_location_to_inc': self.allow_location_to_inc,
            
            }
        if type > 0:
            val.update({
                'uom_id': self.uom_id.get_info(),
                'qty_available': self.qty_available,
                'virtual_available': self.virtual_available,
                'qty_available_not_res': self.qty_available_not_res
            })
        
        if type > 1:
            if self.analytic_tag_id:
                analytic_tag_id = {'id': self.analytic_tag_id.id, 'name': self.analytic_tag_id.display_name}
            else:
                analytic_tag_id = {}
            def_loc = self.get_default_location_putaway()
            val.update ({
                'qty_available': self.qty_available,
                'virtual_available': self.virtual_available,
                'analytic_tag_id': analytic_tag_id,
                'display_name': self.display_name,
                'default_location': def_loc.get_info(),
                'weight': self.weight,
                'volume': self.volume,
                'avisos': {
                    'internal': self.description, 
                    'clientes': self.description_sale,
                    'proveedores': self.description_purchase,
                    'entregas': self.description_pickingout,
                    'recepciones': self.description_pickingin,
                    'picking': self.description_picking
                }
            })
        

        _logger.info(val)
        return val

    @api.model
    def update_default_location(self, values):
        ## product_id = values.get('product_id', False)
        ## location_id = values.get('location_id', False)
        location = self.env['stock.location'].browse( values.get('location_id', False))
        if not location:
            raise ValidationError("No se ha especificado ubicación")
        product = self.env['product.product'].browse(values.get('product_id', False))
        if not product:
            raise ValidationError("No se ha especificado producto")
        return product._update_default_location(location)

    
    def _update_default_location(self, location):
        location_id = location.id

        ##Busco el utaway
        strategy = False
        loc_name = location.display_name
        product_tmpl_id = self.product_tmpl_id

        while not strategy and location:
            if location.putaway_strategy_id.method == 'per_product':
                strategy = location.putaway_strategy_id
            location = location.location_id
        _logger.info("Estableciendo %s por defecto para %s"%(loc_name, self.display_name))

        if strategy:
            vals = {
                'fixed_location_id': location_id,
                'product_product_id': self.id,
                'putaway_id': strategy.id,
                'product_tmpl_id': product_tmpl_id.id,
                'sequence': 0
            }
            domain = [('putaway_id', '=', strategy.id), ('product_product_id', '=', self.id)]
            create = True
            for putaway_id in self.env['stock.product.putaway.strategy'].search(domain):
                if putaway_id.fixed_location_id == location:
                    putaway_id.sequence = 0
                    create = False
                    _logger.info(">>>> Actualizada")
                else:
                    putaway_id.sequence += 1
            if create:
                strat_id = self.env['stock.product.putaway.strategy'].create(vals)
                _logger.info(">>>> Nueva")
            return True
        return ('No se ha encontrado ninguna estrategia')    

