##############################################################################
#
#    Copyright (C) 2004-TODAY
#    Comunitea Servicios Tecnológicos S.L. (https://www.comunitea.com)
#    All Rights Reserved
#    $Javier Colmenero Fernández$
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
    local_mode = fields.Boolean('Modo local', default=True,
                                help="Si es activado, el módulo no realizará "
                                     "conexiones al ftp. Solo trabajará con "
                                     "los ficheros y documentos pendientes "
                                     "de importación")
    ftpbox_path = fields.Char('Ruta ftpbox', required=True)

    @api.model
    def get_configuration(self):
        ids = self.search([])
        if not ids:
            raise exceptions.Warning(_("No hay una configuracion EDI. "))
        else:
            return ids[0]


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    edi_docs = fields.One2many('edi.doc', 'sale_order_id', 'Documento EDI',
                               copy=False)
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

    def action_cancel(self):
        self.write({'funcion_mode': '1'})
        return super().action_cancel()

    @api.multi
    def _action_confirm(self):
        super()._action_confirm()
        self.write({'funcion_mode': '0'})

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals['num_contract'] = self.num_contract
        invoice_vals['note'] = self.note
        return invoice_vals

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        invoice_ids = super().action_invoice_create(grouped=grouped,
                                                    final=final)
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            orders = invoice.invoice_line_ids.mapped('sale_line_ids.order_id')
            if orders:
                invoice.note = ", ".join([x.note for x in
                                          orders.filtered('note')])
            num_contract = invoice.num_contract
            for sale in orders:
                if sale.num_contract and sale.num_contract not in num_contract:
                    if not num_contract:
                        num_contract = sale.num_contract
                    else:
                        num_contract += ", " + sale.num_contract
            if num_contract and num_contract != invoice.num_contract:
                invoice.num_contract = num_contract

        return invoice_ids


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    refcli = fields.Char('Ref. Cliente', size=80)
    refprov = fields.Char('Ref. Proveedor', size=80)
    notes = fields.Text('Notas')

    @api.model
    def create(self, vals):
        if vals.get('product_id', False) and not vals.get('refcli', False) \
                and not vals.get('refprov', False):
            prod = self.env['product.product'].browse(vals['product_id'])
            vals.update({'refcli': prod.refcli, 'refprov': prod.refprov})
        return super().create(vals)

    @api.multi
    def write(self, vals):
        for line in self:
            if vals.get('product_id', False):
                new_prod = self.env['product.product'].\
                    browse(vals['product_id'])
                if new_prod.id != line.product_id.id:
                    vals.update({'refcli': new_prod.refcli,
                                 'refprov': new_prod.refprov})
        return super().write(vals)


class ProductProduct(models.Model):

    _inherit = 'product.product'

    ean13v = fields.Char('EAN13v', size=80)
    refcli = fields.Char('Ref. Cliente', size=80)
    refprov = fields.Char('Ref. Proveedor', size=80)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        recs = self.browse()
        if name:
            recs = self.search([('refcli', operator, name)])
            recs |= self.search([('refprov', operator, name)])

        if not recs:
            return super().name_search(name, args=args, operator=operator,
                                       limit=limit)
        else:
            records = super().name_search(name, args=args, operator=operator,
                                          limit=limit)
            records = [x[0] for x in records]
            records = self.browse(records)
            recs |= records
            return recs.name_get()


class ProductTemplate(models.Model):

    _inherit = "product.template"

    refcli = fields.Char('Ref. Cliente', related="product_variant_ids.refcli")
    refprov = fields.Char('Ref. Proveedor',
                          related="product_variant_ids.refprov")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gln = fields.Char('GLN', size=80,
                      help="Numero de localizacion global: esta destinado a "
                           "la identificacion inequivoca y no ambigua de "
                           "Locaciones fisicas, legales o funcionales")
    customer_reference = fields.\
        Char('Código de referencia', size=80,
             help="Es el código en que le identifica en el sistema del "
                  "cliente, normalmente es el id de cliente o de id de "
                  "proveedor que este le asigna.")
    edi_relation = fields.Selection([('GC', 'Gran consumo'),
                                     ('MC', 'Mercancia general')],
                                    'Tipo de relacion')
    edi_operational_code = fields.Char('Punto operacional')
    center_code = fields.Char('Id. del centro', size=80,
                              help="Codigo de centro, un identificador unico "
                                   "de este centro para el cliente. Este "
                                   "codigo es usado para el envio/recepcion "
                                   "de ficheros EDI, y la impresion de "
                                   "etiquetas.")


class AccountPaymentMode(models.Model):

    _inherit = 'account.payment.mode'

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
    edi_docs = fields.One2many('edi.doc', 'picking_id', 'Documentos EDI',
                               copy=False)


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

    def _assign_picking(self):
        res = super()._assign_picking()
        for pick in self.mapped('picking_id').filtered('sale_id'):
            pick.write({'num_contract': pick.sale_id.num_contract,
                        'note': pick.sale_id.note})
        return res


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
    def _get_refund_prepare_fields(self):
        res = super()._get_refund_prepare_fields()
        res.extend(['num_contract', 'note'])
        return res
