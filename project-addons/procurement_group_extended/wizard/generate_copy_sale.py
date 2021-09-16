# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
import os
import time

class GenerateSaleCopyLines(models.TransientModel):
    
    _name = "generate.sale.copy.line"

    partner_id = fields.Many2one('res.partner', string="Entrega")
    ref_client = fields.Char(string="Referencia de cliente")
    generate_id = fields.Many2one('generate.sale.copy', string="Wizard")
    
class GenerateSaleCopy(models.TransientModel):

    _name = "generate.sale.copy"

    sale_id = fields.Many2one('sale.order', string="sale to copy")
    partner_id = fields.Many2one(related="sale_id.partner_id")
    group_id = fields.Many2one('procurement.group', string="Grupo de abastecimiento")
    destination_code = fields.Boolean('Codigo de destino', help="If true, el destino será un codigo de destino\n Desmarcado: 1 venta, varias entregas, 1 factura\n Marcado: Varias ventas, varios albaranes, varias facturas")
    merge_moves = fields.Boolean("Separación de movimientos comunes por venta")
    line_ids  = fields.One2many('generate.sale.copy.line', 'generate_id',string="Lineas")
    child_ids = fields.One2many(related="partner_id.child_ids")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        sale_id = self.env['sale.order'].browse(self._context.get('active_id'))
        if sale_id.state in ['sale', 'locked']:
            raise ValidationError ('No se puede duplicar pedidos ya realizados')
        if sale_id:
            res['sale_id'] = sale_id.id
            res['partner_id'] = sale_id.partner_id.id
            res['group_id']=sale_id.procurement_group_id.id
        return res

    @api.multi
    def generate_sales(self):
        if self.destination_code:
            ## se copian las líneas.
            self.sale_id.merge_moves = self.merge_moves
            lines_to_copy = self.sale_id.order_line
            for wzd_line in self.line_ids:
                for line in lines_to_copy:
                    values = {'order_id': self.sale_id.id, 
                              'destination_code_id': wzd_line.partner_id.id}
                    new_sale_line = line.copy(values)

        else:
            for wzd_line in self.line_ids:
                copy_vals = {
                    'partner_shipping_id':wzd_line.partner_id.id,
                    'client_order_ref': wzd_line.ref_client,
                    'procurement_group_id': self.group_id.id
                }
                new_sale = self.sale_id.copy(copy_vals)
                
        return True