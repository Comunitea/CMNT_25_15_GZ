# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-TODAY
#        Pexego Sistemas Informáticos (http://www.pexego.es) All Rights Reserved
#        $Javier Colmenero Fernández$
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

from odoo import models, fields, _, api, exceptions
from odoo.addons import decimal_precision as dp


class EdiDoc(models.Model):
    _name = "edi.doc"
    _description = "Documento EDI"

    name = fields.Char('Referencia', required=True)
    file_name = fields.Char('Nombre fichero', size=64)
    type = fields.Selection([('orders', 'Pedido'),
                             ('ordrsp', 'Respuesta Pedido'),
                             ('desadv', 'Albarán'),
                             ('recadv', 'Confirmación mercancia'),
                             ('invoic', 'Factura')], 'Tipo de documento',
                            index=1)
    date = fields.Datetime('Descargado el')
    date_process = fields.Datetime('Procesado el')
    status = fields.Selection([('draft', 'Sin procesar'),
                               ('imported', 'Importado'),
                               ('export', 'Exportado'),
                               ('error', 'Con incidencias')], 'Estado',
                              index=1)
    mode = fields.Selection([('ORI', 'ORI'), ('DEL', 'DEL'), ('REP', 'REP'),
                             ('1', 'Aceptado'), ('2', 'No Aceptado'),
                             ('3', 'Cambiado'), ('9', 'Original'),
                             ('7', 'Duplicado'), ('31', 'Copia'),
                             ('5', 'Remplazo')], 'Modo', readonly=True,
                            index=1)
    sale_order_id = fields.Many2one('sale.order', 'Pedido',
                                    ondelete='restrict')
    picking_id = fields.Many2one('stock.picking', 'Albaran',
                                 ondelete='restrict')
    invoice_id = fields.Many2one('account.invoice', 'Factura',
                                 ondelete='restrict')
    response_document_id = fields.Many2one('edi.doc', 'Documento de respuesta')
    send_response = fields.Char('Respuesta', index=1)
    send_date = fields.Datetime('Fecha del ultimo envio', index=1)
    message = fields.Text('Mensaje')
    gln_e = fields.Char('GLN Emisor', size=60,
                        help="GLN del emisor del documento")
    gln_v = fields.Char('GLN vendedor', size=60,
                        help="GLN del receptor del documento")
    gln_c = fields.Char('GLN comprador', size=60,
                        help="GLN de la dirección de factura")
    gln_r = fields.Char('GLN receptor', size=60,
                        help="GLN de la dirección de envio")

    _order = 'date desc'


class EdiConfiguration(models.Model):
    _name = "edi.configuration"
    _description = "Configuracion EDI"

    name = fields.Char('Nombre', required=True)
    salesman = fields.Many2one('res.users', 'Comercial para los pedidos.',
                               help="Seleccione el comercial que será asignado"
                                    " a todos los pedidos.")
    ftp_host = fields.Char('Host')
    ftp_port = fields.Char('Puerto', size=6)
    ftp_user = fields.Char('Usuario')
    ftp_password = fields.Char('Password')
    local_mode = fields.Boolean('Modo local',
                                help="Si es activado, el módulo no realizará "
                                     "conexiones al ftp. Solo trabajará con "
                                     "los ficheros y documentos pendientes "
                                     "de importación")
    ftpbox_path = fields.Char('Ruta ftpbox', required=True)


    def default_get(self, cr, uid, fields, context=None):
        res = super(edi_configuration, self).default_get(cr, uid, fields, context=context)
        res.update({'local_mode': True})
        return res

    def get_configuration(self,cr,uid,ids):

        ids = self.pool.get('edi.configuration').search(cr, uid, [])
        if not ids:
            raise exceptions.Warning(_("No hay una configuracion EDI. "))
        else :
            return self.pool.get('edi.configuration').browse(cr,uid,ids[0])


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    edi_docs = fields.One2many('edi.doc', 'sale_order_id', 'Documento EDI')
    order_type = fields.Selection([('ORI', 'ORI'), ('REP', 'REP'),
                                   ('DEL', 'DEL')], 'Tipo', readonly=True)
    funcion_mode = fields.Selection([('0', 'Aceptación ORDERS'),
                                     ('1', 'Rechazo ORDERS'),
                                     ('2', 'Oferta alternativa'),
                                     ('3', 'Valoración ORDERS')], 'Funcion',
                                    copy=False)
    top_date = fields.Date('Fecha limite')
    urgent = fields.Boolean('Urgente')
    num_contract = fields.Char('Contract Number', size=128)
    partner_unor_id = fields.Many2one('res.partner', 'UNOR EDI')

    def copy(self, cr, uid, id, default=None, context=None):
        """ sobrescribimos el copy para que no duplique los documentos"""
        if not default:
            default = {}
        default.update({
            'edi_docs': [],
        })
        return super(SaleOrder, self).copy(cr, uid, id, default, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale = self.pool.get('sale.order').write(cr,uid,ids,{'funcion_mode' : '1'},context=context)
        return super(SaleOrder, self).action_cancel(cr, uid, ids,context=context)

    def action_ship_create(self, cr, uid, ids, *args):
        sale = self.pool.get('sale.order').write(cr,uid,ids,{'funcion_mode' : '0'})
        return super(SaleOrder, self).action_ship_create(cr, uid, ids,*args)

    def _prepare_procurement_group(self, cr, uid, order, context=None):
        res = super(SaleOrder, self)._prepare_procurement_group(cr, uid, order, context=None)
        res.update({'num_contract': order.num_contract or ''})
        res.update({'note': order.note or ''})
        return res


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    refcli = fields.Char('Ref. Cliente', size=80)
    refprov = fields.Char('Ref. Proveedor', size=80)
    notes = fields.Text('Notas')

    def create(self, cr, uid, values, context=None):
        if values.get('product_id',False) and not values.get('refcli',False) and not values.get('refprov',False):
            prod = self.pool.get('product.product').browse(cr,uid,values['product_id'])
            values.update({'refcli': prod.refcli,'refprov':prod.refprov})
        return super(SaleOrderLine, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        for line in self.pool.get('sale.order.line').browse(cr,uid,ids):
            if values.get('product_id',False):
                new_prod = self.pool.get('product.product').browse(cr,uid,values['product_id'])
                if new_prod.id != line.product_id.id:
                    values.update({'refcli': new_prod.refcli,'refprov':new_prod.refprov})
        return super(SaleOrderLine, self).write(cr, uid, ids, values, context=context)


class ProductProduct(models.Model):

    _inherit = 'product.product'

    ean13v = fields.Char('EAN13v', size=80)
    refcli = fields.Char('Ref. Cliente', size=80)
    refprov = fields.Char('Ref. Proveedor', size=80)

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        ids = []
        if name:
            ids = self.search(cr, user, [('refcli', operator, name)])
            ids.extend(self.search(cr, user, [('refprov', operator, name)]))

        if not ids:
            return super(ProductProduct, self).name_search(cr, user, name=name, args=args, operator=operator, context=context, limit=limit)
        else:
            records = super(ProductProduct, self).name_search(cr, user, name=name, args=args, operator=operator, context=context, limit=limit)
            new_ids = [x[0] for x in records]
            ids.extend(new_ids)
            ids = list(set(ids))
            return self.name_get(cr, user, ids, context=context)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gln = fields.Char('GLN', size=80,
                      help="Numero de localizacion global: esta destinado a "
                           "la identificacion inequivoca y no ambigua de "
                           "Locaciones fisicas, legales o funcionales")
    customer_reference = fields.\
        Char('Codigo de referencia', size=80,
             help="Es el código en que le identifica en el sistema del "
                  "cliente, normalmente es el id de cliente o de id de "
                  "proveedor que este le asigna.")
    edi_relation = fields.Selection([('GC', 'Gran consumo'),
                                     ('MC', 'Mercancia general')],
                                    'Tipo de relacion')
    edi_operational_code = fields.Char('Punto operacional')
    fiscal_position = fields.Many2one('account.fiscal.position',
                                      "Posicion Fiscal",
                                      company_dependant=True,
                                      help="The fiscal position will determine"
                                           " taxes and the accounts used for "
                                           "the partner.")
    center_code = fields.Char('Id. del centro', size=80,
                              help="Codigo de centro, un identificador unico "
                                   "de este centro para el cliente. Este "
                                   "codigo es usado para el envio/recepcion "
                                   "de ficheros EDI, y la impresion de "
                                   "etiquetas.")


class PaymentMode(models.Model):

    _inherit = 'payment.mode'

    edi_code = fields.Selection([('42', 'A una cuenta bancaria'),
                                 ('14E', 'Giro bancario'),
                                 ('10', 'En efectivo'), ('20', 'Cheque'),
                                 ('60', 'Pagaré')], 'Codigo EDI', index=1)


class ProductUom(models.Model):

    _inherit = 'product.uom'

    edi_code = fields.Char("Codigo edi", size=64)


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    num_contract = fields.Char('Contract Number', size=128)
    note = fields.Text('Notes')
    edi_docs = fields.One2many('edi.doc', 'picking_id', 'Documentos EDI')
    return_picking_id = fields.Many2one('stock.picking',
                                        'Albaran de devolucion', readonly=True)

    def copy(self, cr, uid, id, default=None, context=None):
        """ sobrescribimos el copy para que no duplique los documentos"""
        if not default:
            default = {}
        default.update({
            'edi_docs': [],
            'return_picking_id': False
        })

        return super(StockPicking, self).copy(cr, uid, id, default, context=context)

    def action_invoice_create(self, cr, uid, ids, journal_id=False, group=False, type='out_invoice', context=None):
        """Lanzamos excepción al crear la factura si la posición fiscal de los pedidos de las lineas son diferentes"""
        res = super(StockPicking,self).action_invoice_create(cr, uid, ids, journal_id, group, type,context) #res diccionario de la forma {id_del_albaran:id_de_la_factura}
        set_fp = set()
        for inv_id in res:  # nos recorremos las facturas diferentes
            inv = self.pool.get('account.invoice').browse(cr,uid,inv_id,context)
            visited_order_ids = []
            for line in inv.invoice_line:
                if line.picking_id:
                    for move in line.picking_id.move_lines:
                        if move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.order_id.id not in visited_order_ids:
                            visited_order_ids.append(move.procurement_id.sale_line_id.order_id.id)
                            set_fp.add(move.procurement_id.sale_line_id.order_id.fiscal_position.id)

            if len(set_fp) > 1: #hay mas de una posición fiscal
                raise exceptions.\
                    UserError(_('Las posiciones fiscales de los pedidos son diferentes'))
            elif set_fp:
                inv.write({'fiscal_position' : list(set_fp)[0] })

        for invoice in res:
            invoice_obj = self.pool['account.invoice'].browse(cr, uid,invoice)
            contract_number = ''
            notes = ''
            if(invoice_obj):
                for pick in invoice_obj.invoice_line:
                    if(pick.picking_id.num_contract):
                        if contract_number:
                            if pick.picking_id.num_contract not in contract_number:
                                contract_number += u', ' + pick.picking_id.num_contract
                        else:
                            contract_number = pick.picking_id.num_contract
                    if(pick.picking_id.note):
                        if notes:
                            if pick.picking_id.note not in notes:
                                notes += u', ' + pick.picking_id.note
                        else:
                            notes += pick.picking_id.note
            invoice_obj.num_contract = contract_number
            invoice_obj.note = notes
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def _get_sale_line_history(self):
        for move in self:
            if move.sale_line_id:
                move.sale_line_history_id = move.sale_line_id.id
            else:
                self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='stock_move' and (column_name='sale_line_id' or column_name='openupgrade_legacy_8_0_sale_line_id')")
                data = self.env.cr.fetchone()
                if data and data[0]:
                    self.env.cr.execute("select %s from stock_move where id = %s" % (data[0], move.id))
                    data2 = self.env.cr.fetchone()
                    if data2 and data2[0]:
                        move.sale_line_history_id = data2[0]

    acepted_qty = fields.Float('Cantidad aceptada', readonly=True,
                               digits=dp.get_precision('Product UoM'))
    rejected = fields.Boolean('Rechazado')
    sale_line_history_id = fields.\
        Many2one("sale.order.line", compute="_get_sale_line_history")

    _order = 'date desc'

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(StockMove, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        # Actualizamos la cantidad si el movimiento no es de devolución.
        res.update({'quantity': (move.acepted_qty or move.product_qty),
                    'sale_line_id': move.sale_line_history_id and move.sale_line_history_id.id or False})

        if move.rejected and not move.acepted_qty:
            res = {}
        return res

    def _prepare_picking_assign(self, cr, uid, move, context=None):
        values = super(StockMove, self)._prepare_picking_assign(cr, uid, move, context=context)
        values['num_contract'] = move.group_id and move.group_id.num_contract or ''
        values['note'] = move.group_id and move.group_id.note or ''

        return values

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    num_contract = fields.Char('Contract Number', size=128)
    note = fields.Text('Notes')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    num_contract = fields.Char('Contract Number', size=128)
    note = fields.Text('Notes')
    edi_docs = fields.One2many('edi.doc', 'invoice_id', 'Documentos EDI')
    gi_cab_nodo = fields.Selection([('380', 'Comercial'),
                                    ('381', 'Nota de crédito'),
                                    ('383', 'Nota de débito')], 'Nodo',
                                   default='380')
    gi_cab_funcion = fields.Selection([('9', 'Original'), ('7', 'Duplicado'),
                                       ('31', 'Copia'), ('5', 'Remplazo')],
                                      'Funcion', default='9')

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        vals = super(AccountInvoice, self)._prepare_refund(invoice, date=date,
                                                            period_id=period_id,
                                                            description=description,
                                                            journal_id=journal_id)
        vals["num_contract"] = invoice.num_contract
        vals["note"] = invoice.note
        return vals

#TODO: Migrar
# ~ class AccountInvoiceLine(models.Model):

    # ~ _inherit = "account.invoice.line"

    # ~ _columns = {
        # ~ 'sale_line_id' : fields.many2one('sale.order.line','Sale line', readonly=True),
    # ~ }

#TODO: Migrar
# ~ class stock_return_picking(models.TransientModel):
    # ~ _inherit = 'stock.return.picking'

    # ~ def default_get(self, cr, uid, fields, context=None):
        # ~ """ Precargamos el campo cantidad con la diferencia entre la cantidad, y la cantidad
        # ~ aceptada del movimiento"""
        # ~ if context is None:
            # ~ context = {}

        # ~ result1 = []
        # ~ res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
        # ~ record_id = context and context.get('active_id', False) or False
        # ~ pick_obj = self.pool.get('stock.picking')
        # ~ pick = pick_obj.browse(cr, uid, record_id, context=context)

        # ~ if pick:
            # ~ for line in pick.move_lines:
                # ~ qty = line.product_qty - line.acepted_qty ##el return history k?? qty = line.product_qty - return_history[line.id]
                # ~ if qty > 0:
                    # ~ result1.append({'product_id': line.product_id.id, 'quantity': qty,'move_id':line.id})
            # ~ if 'product_return_moves' in fields:
                # ~ res.update({'product_return_moves': result1})

        # ~ return res

    # ~ def create_returns(self, cr, uid, ids, context=None):
        # ~ """ Escribimos el albaran de devolución relacionado al albarán original"""
        # ~ res = super(stock_return_picking,self).create_returns(cr,uid,ids,context)

        # ~ record_id = context and context.get('active_id', False) or False
        # ~ pick = self.pool.get('stock.picking').browse(cr, uid, record_id, context=context)

        # ~ if pick:
            # ~ return_pick_id = self.pool.get('stock.picking').search(cr,uid,[('name','like',"%"+pick.name+"-return")],context=context)
            # ~ if return_pick_id:
                # ~ pick.write({'return_picking_id':return_pick_id[0]})

        # ~ return res
