from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit='stock.inventory'

    @api.model
    def get_lots_apk(self, values):

    
        product_id = values.get('product_id', False)
        location_id = values.get('location_id', False)
        if not location_id:
            location_id = self.env['stock.warehouse'].browse(self._context['warehouse_id']).lot_stock_id.id
        lot_id = values.get('lot_id', False)
        lot_name = values.get('lot_name', False)
        package_id = values.get('package_id', False)
        locations = self.env['stock.location'].search([('id', 'child_of', [location_id])])
        domain = ' sq.location_id in %s AND pp.active'
        args = (tuple(locations.ids),)
        vals = []
        Product = self.env['product.product']
        # case 0: Filter on company
        if self.env.user.company_id:
            domain += ' AND sq.company_id = %s'
            args += (self.env.user.company_id.id,)
        """ NO APLICA
        #case 1: Filter on One owner only or One product for a specific owner
        if self.partner_id:
            domain += ' AND sq.owner_id = %s'
            args += (self.partner_id.id,)
        """
        #case 2: Filter on One Lot/Serial Number
        if lot_name:
            domain += " AND spl.name ilike %s"
            args += (lot_name,)
        if lot_id:
            domain += ' AND sq.lot_id = %s'
            args += (lot_id,)
        #case 3: Filter on One product
        if product_id:
            domain += ' AND sq.product_id = %s'
            args += (product_id,)
        #case 4: Filter on A Pack
        if package_id:
            domain += ' AND sq.package_id = %s'
            args += (package_id,)
        """ NO APLICA
        #case 5: Filter on One product category + Exahausted Products
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND sq.product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products
        """
        self.env.cr.execute("""SELECT sq.product_id as product_id, sum(quantity) as product_qty,
            sq.location_id as location_id, sq.lot_id as prod_lot_id, sq.package_id as package_id,
            sq.owner_id as partner_id
            FROM stock_quant sq
            LEFT JOIN product_product pp
            ON pp.id = sq.product_id
            left join stock_production_lot spl 
            ON spl.id = sq.lot_id
            WHERE %s
            GROUP BY sq.product_id, sq.location_id, sq.lot_id, sq.package_id, sq.owner_id """ % domain, args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                #quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)

        Lots = self.env['stock.production.lot'] 
        res = []
        for val in vals:
            lot_id = val['prod_lot_id']
            lot = Lots.filtered(lambda x: x.id == lot_id)
            if not lot:
                lot = Lots.browse(lot_id)
            res.append(lot.get_info())
        return res

    @api.model
    def get_lines_apk(self, values):
        product_id = values.get('product_id', False)
        location_id = values.get('location_id', False)
        if not location_id:
            location_id = self.env['stock.warehouse'].browse(self._context['warehouse_id']).lot_stock_id.id
        lot_id = values.get('lot_id', False)
        package_id = values.get('package_id', False)

        locations = self.env['stock.location'].search([('id', 'child_of', [location_id])])
        domain = ' sq.location_id in %s AND pp.active'
        args = (tuple(locations.ids),)

        vals = []
        Product = self.env['product.product']

        # case 0: Filter on company
        if self.env.user.company_id:
            domain += ' AND sq.company_id = %s'
            args += (self.env.user.company_id.id,)
        """ NO APLICA
        #case 1: Filter on One owner only or One product for a specific owner
        if self.partner_id:
            domain += ' AND sq.owner_id = %s'
            args += (self.partner_id.id,)
        """
        #case 2: Filter on One Lot/Serial Number
        if lot_id:
            domain += ' AND sq.lot_id = %s'
            args += (lot_id,)
        #case 3: Filter on One product
        if product_id:
            domain += ' AND sq.product_id = %s'
            args += (product_id,)
        #case 4: Filter on A Pack
        if package_id:
            domain += ' AND sq.package_id = %s'
            args += (package_id,)
        """ NO APLICA
        #case 5: Filter on One product category + Exahausted Products
        if self.category_id:
            categ_products = Product.search([('categ_id', '=', self.category_id.id)])
            domain += ' AND sq.product_id = ANY (%s)'
            args += (categ_products.ids,)
            products_to_filter |= categ_products
        """
        self.env.cr.execute("""SELECT sq.product_id as product_id, sum(quantity) as product_qty,
            sq.location_id as location_id, sq.lot_id as prod_lot_id, sq.package_id as package_id,
            sq.owner_id as partner_id
            FROM stock_quant sq
            LEFT JOIN product_product pp
            ON pp.id = sq.product_id
            WHERE %s
            GROUP BY sq.product_id, sq.location_id, sq.lot_id, sq.package_id, sq.owner_id """ % domain, args)

        for product_data in self.env.cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for void_field in [item[0] for item in product_data.items() if item[1] is None]:
                product_data[void_field] = False
            product_data['theoretical_qty'] = product_data['product_qty']
            if product_data['product_id']:
                product_data['product_uom_id'] = Product.browse(product_data['product_id']).uom_id.id
                #quant_products |= Product.browse(product_data['product_id'])
            vals.append(product_data)
        
        Products = self.env['product.product']
        ProductInfo = {}
        LocationInfo = {}
        UomInfo = {}
        LotInfo = {}
        Locations = self.env['stock.location']
        Uoms = self.env['product.uom']

        Lots = self.env['stock.production.lot'] 
        res = []
        for val in vals:
            location_id = val['location_id']
            location = Locations.filtered(lambda x: x.id == location_id)
            if not location:
                location = Locations.browse(location_id)
                LocationInfo[location.id] = location.get_info()
                locations |= location

            product_id = val['product_id']
            product = Products.filtered(lambda x: x.id == product_id)
            if not product:
                product = Products.browse(product_id)

                ProductInfo[product.id] = product.get_info()
                UomInfo[product.uom_id.id] = product.uom_id.get_info()
                Products |= product

            lot_id = val['prod_lot_id']
            lot = Lots.filtered(lambda x: x.id == lot_id)
            if not lot:
                lot = Lots.browse(lot_id)
                if lot:
                    LotInfo[lot.id] = lot.get_info()
                    Lots |= lot

            line_vals = {
                'location_id': LocationInfo[location_id],
                'product_id': ProductInfo[product_id],
                'product_uom_id':UomInfo[product.uom_id.id],
                'prod_lot_id': lot and LotInfo[lot_id] or False,
                'theoretical_qty': val['product_qty'],
                'product_qty':  val['product_qty'],
                'hide': False,
            }
            _logger.info(line_vals)
            res.append(line_vals)
        return res
        
    @api.model
    def add_line_apk(self, values):
        product_id = values.get('product_id', False)
        product = self.env['product.product'].browse(product_id)
        location_id = values.get('location_id', False)
        lot_id = values.get('lot_id', False)
        lot_name = values.get('lot_name', '')
        th_qty = product.with_context(location=location_id, lot_id=lot_id and lot_id.id or False).qty_available
        if product.tracking == 'serial' and (lot_name or lot_id):
            product_qty = 1
        else:
            product_qty = 0
        vals = {
            'id': 0,
            'location_id': self.env['stock.location'].browse(location_id).get_info(),
            'product_id': product.get_info(),
            'product_uom_id':product.uom_id.get_info(),
            'prod_lot_id': lot_id and lot_id.get_info() or {'id': 0, 'name': lot_name},
            'theoretical_qty': th_qty,
            'product_qty': product_qty,
            'hide': False,
        }
        print(vals)
        return vals

    
    @api.model
    def set_default_location(self, values):

        product_id = values.get('product_id', False)
        location_id = values.get('location_id', False)
        location = self.env['stock.location'].browse(location_id)
        product = self.env['product.product'].browse(product_id)
        return product._set_default_location(location)

        ##Busco el utaway
        strategy = False
        loc_name = location.display_name
        product_tmpl_id = product.product_tmpl_id

        while not strategy and location:
            if location.putaway_strategy_id.method == 'per_product':
                strategy = location.putaway_strategy_id
            location = location.location_id
        _logger.info("Estableciendo %s por defecto para %s"%(loc_name, product.display_name))
        if strategy:
            vals = {
                'fixed_location_id': location_id,
                'product_product_id': product_id,
                'putaway_id': strategy.id,
                'product_tmpl_id': product_tmpl_id.id,
                'sequence': 0
            }
            domain = [('putaway_id', '=', strategy.id), ('product_product_id', '=', product_id)]
            create = True
            for putaway_id in self.env['stock.product.putaway.strategy'].search(domain):
                if putaway_id.fixed_location_id.id == location_id:
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

    @api.model
    def apk_inventory(self, values):
        line_data = values.get('line_values')
        action_done = values.get('action_done', False)
        product_ids = []
        location_ids = []
        
        for line in line_data:
            if not line['product_id'] in product_ids:
                product_ids += [line['product_id']]
            if not line['location_id'] in location_ids:
                location_ids += [line['location_id']]
        if len(location_ids) == 1:
            location_id = location_ids[0]
        else:
            location_id = self.env['stock.warehouse'].browse(self._context.get('warehouse_id')).lot_stock_id.id
        
        if len(product_ids) != 1:
            product_id = False
            filter_type = 'none'
        else:
            filter_type = 'product'
            product_id = product_ids[0]
        vals = self.default_get(self._fields.keys())
        vals.update({
            'name': 'APK: {}'.format(fields.Datetime.now()),
            'filter': filter_type, 
            'exhausted': False,
            'company_id': self.env.user.company_id.id,
            'state': 'confirm',
            'location_id': location_id})
        if product_id:
            vals['product_id'] = product_id
        inv_id = self.env['stock.inventory'].create(vals)
        ### inv_id.action_start()

        for line in line_data:
            if not line['prod_lot_id'] and line['prod_lot_name']:
                lot_domain = [('name', '=', line['prod_lot_name']), ('product_id', '=', line['product_id'])]
                lot_id = self.env['stock.production.lot'].search(lot_domain, limit=1)
                if not lot_id:
                    lot_id = self.env['stock.production.lot'].create({'name': line['prod_lot_name'], 'ref': line['prod_lot_name']})
                line['prod_lot_id'] = lot_id.id

            line['inventory_id'] = inv_id.id
            self.env['stock.inventory.line'].create(line)
        _logger.info("Se ha creado el inventario %s"%inv_id.name)
        if action_done:
            inv_id.action_done()
            _logger.info(">>> Validado")
        return True

    @api.model
    def ik(self, values):
        product_id = values.get('product_id', False)
        location_id = values.get('location_id', False)
        if product_id:
            filter_type = 'product'
        else:
            filter_type = 'none'
        domain = [('state', 'in', ['draft', 'confirm']), ('filter', '=', filter_type), ('location_id', '=', location_id)]
        if product_id:
            domain += [('product_id', '=', product_id)]
        inv_id = self.search(domain, limit=1)
        if not inv_id:
            vals = self.default_get(self._fields.keys())
            vals.update({
                'name': 'APK: {}'.format(fields.Datetime.now()),
                'filter': filter_type, 
                'exhausted': False,
                'company_id': self.env.user.company_id.id,
                'location_id': location_id})
            if product_id:
                vals['product_id'] = product_id

            inv_id = self.env['stock.inventory'].create(vals)
        
        if inv_id.state == 'draft':
            inv_id.action_start()
        
        res = []
        for line in inv_id.line_ids:
            line_vals = {
                'id': line.id, 
                'location_id': line.location_id.get_info(),
                'product_id': line.product_id.get_info(),
                'product_uom_id':line.product_uom_id.get_info(),
                'prod_lot_id': line.prod_lot_id and line.prod_lot_id.get_info() or False,
                'theoretical_qty': line.theoretical_qty,
                'product_qty': line.product_qty,
                'hide': False,

            }
        
            res.append(line_vals)
        print (res)
        return res