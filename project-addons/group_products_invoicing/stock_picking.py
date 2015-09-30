# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011 Pexego Sistemas Informáticos. All Rights Reserved
#    $Javier Colmenero Fernández$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, fields

class stock_picking(orm.Model):
    _inherit = 'stock.picking'

    def action_invoice_create(self, cr, uid, ids, journal_id=False, group=False, type='out_invoice', context=None):
        """ Agrupamos las lineas de una factura, si proceden de la misma linea de venta y el producto
        es el mismo"""
        res = super(stock_picking,self).action_invoice_create(cr, uid, ids, journal_id, group, type,context)
        for inv_id in res:
            inv = self.pool.get('account.invoice').browse(cr,uid,inv_id,context)
            if inv.type in ('out_invoice', 'out_refund'):
                dlin = {}  # diccionario con las lineas agrupando sus cantidades
                del_lines = [] #lista de lineas a borrar
                for line in inv.invoice_line:
                    if line.sale_line_id.id not in dlin:
                        dlin[line.sale_line_id.id] = [line,line.quantity]
                    else:
                        dlin[line.sale_line_id.id][1] +=  line.quantity #sumamos la cantidad porque procede de la misma sale_line_id
                        del_lines.append(line.id) #añadimos el id de la linea para borrarlo despues
                for list_obj in dlin.values():
                    inv_line,list_qty = list_obj
                    if inv_line.quantity < list_qty: #si la cantidad de la linea es menor que la agrupada, la actualizamos
                        inv_line.write( {'quantity' : list_qty} )
                self.pool.get('account.invoice.line').unlink(cr,uid,del_lines) #borramos las lineas que sobran
        return res


class stock_move(orm.Model):

    _inherit = "stock.move"

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        if inv_type in ('out_invoice', 'out_refund'):
            if move.procurement_id and move.procurement_id.sale_line_id:
                res['sale_line_id'] = move.procurement_id.sale_line_id.id
            elif move.sale_line_history_id:
                sale_line = move.sale_line_history_id
                res['sale_line_id'] = sale_line.id
                res['invoice_line_tax_id'] = [(6, 0, [x.id for x in sale_line.tax_id])]
                res['account_analytic_id'] = sale_line.order_id.project_id and sale_line.order_id.project_id.id or False
                res['discount'] = sale_line.discount
                if move.product_id.id != sale_line.product_id.id:
                    res['price_unit'] = self.pool['product.pricelist'].price_get(
                        cr, uid, [sale_line.order_id.pricelist_id.id],
                        move.product_id.id, move.product_uom_qty or 1.0,
                        sale_line.order_id.partner_id, context=context)[sale_line.order_id.pricelist_id.id]
                else:
                    res['price_unit'] = sale_line.price_unit
                uos_coeff = move.product_uom_qty and move.product_uos_qty / move.product_uom_qty or 1.0
                res['price_unit'] = res['price_unit'] / uos_coeff
        return res

    def _get_sale_line_history(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None: context = {}
        for move in self.browse(cr, uid, ids, context=context):
            if move.procurement_id:
                if move.procurement_id.sale_line_id:
                    res[move.id] = move.procurement_id.sale_line_id.id
                else:
                    res[move.id] = False
            else:
                cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='stock_move' and (column_name='sale_line_id' or column_name='openupgrade_legacy_8_0_sale_line_id')")
                data = cr.fetchone()
                if data and data[0]:
                    cr.execute("select %s from stock_move where id = %s" % (data[0], move.id))
                    data2 = cr.fetchone()
                    if data2 and data2[0]:
                        res[move.id] = data2[0]
                    else:
                        res[move.id] = False
                else:
                    res[move.id] = False
        return res


    _columns = {
        'sale_line_history_id': fields.function(_get_sale_line_history, type="many2one", relation="sale.order.line", readonly=True)
    }


class account_invoice_line(orm.Model):
    """Añadimos el campo sale_line_id a la linea de factura"""
    _inherit = 'account.invoice.line'
    _columns = {
        'sale_line_id' : fields.many2one('sale.order.line','Sale line', readonly=True),
    }

