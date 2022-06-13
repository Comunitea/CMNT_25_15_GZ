# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# TODO vista para ver errorres o devolver resultados

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import xlrd
import base64

import logging
_logger = logging.getLogger(__name__)

# Global variable to store the new created templates
template_ids = []

states = {
    'Petición presupuesto': 'draft', 
    'Petición de cotización enviada': 'sent',
    'Para aprobar': 'to approve',
    'Pedido de compra': 'purchase',
    'Bloqueado': 'done',
    'Cancelado': 'cancel'}

class PurchaseImportWzd(models.TransientModel):
    _name = 'purchase.import.wzd'

    name = fields.Char('Importation name', required=True)
    file = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Filename')

    @api.onchange('file')
    def onchange_filename(self):
        if not self.name and self.filename:
            self.name = self.filename and self.filename.split('.')[0]
    
    def _logger_error(self, msg):
        _logger.info(_(' ---------------------------------\n  %s\n --------------------------------')%msg)

    def create_from_row_vals(self, vals):
        _logger.info("\n>>>>>>>>>>>> CREANDO LA COMPRA %s" %vals['name'])
        partner_id =  self.get_id_from_xml_id(vals['partner_id'])
        msg = ''
        if not partner_id:
            partner_id = self.env['res.partner'].browse(8278)
            msg = '%s\n%s'%(msg, "Error en partner %s"% vals['partner_id'])

        global_analytic_id = self.env['account.analytic.account'].browse(vals['global_analytic_id'])
        if vals['global_analytic_id'] and not global_analytic_id:
            msg = '%s\n%s'%(msg, "Error en analitica %s"% vals['global_analytic_id'])
        
        global_analytic_tag_id = self.env['account.analytic.tag'].browse(vals['global_analytic_tag_id']) 
        ##self.get_id_from_xml_id(vals['global_analytic_tag_id'])
        if vals['global_analytic_tag_id'] and not global_analytic_tag_id:
            msg = '%s\n%s'%(msg, "Error en global_analytic_tag_id %s"% vals['global_analytic_tag_id'])

        picking_type_id_ = self.env['stock.picking.type'].browse(vals['picking_type_id_']) 
        if vals['picking_type_id_'] and not picking_type_id_:
            msg = '%s\n%s'%(msg, "Error en picking_type_id_ %s"% vals['picking_type_id_'])

        payment_term_id = self.env['account.payment.term'].browse(vals['payment_term_id']) ##self.get_id_from_xml_id(vals['payment_term_id'])
        if vals['payment_term_id'] and not payment_term_id:
            msg = '%s\n%s'%(msg, "Error en payment_term_id %s"% vals['payment_term_id'])

        payment_mode_id = self.env['account.payment.mode'].browse(vals['payment_mode_id']) ## self.get_id_from_xml_id(vals['payment_mode_id'])
        if vals['payment_mode_id'] and not payment_mode_id:
            msg = '%s\n%s'%(msg, "Error en payment_mode_id %s"% vals['payment_mode_id'])
        supplier_partner_bank_id = self.env['res.partner.bank'].browse(vals['supplier_partner_bank_id']) ## self.get_id_from_xml_id(vals['supplier_partner_bank_id'])
        if vals['supplier_partner_bank_id'] and not supplier_partner_bank_id:
            msg = '%s\n%s'%(msg, "Error en supplier_partner_bank_id %s"% vals['supplier_partner_bank_id'])
        fiscal_position_id = self.env['account.fiscal.position'].browse(vals['fiscal_position_id']) ## self.get_id_from_xml_id(vals['fiscal_position_id'])
        if vals['fiscal_position_id'] and not fiscal_position_id:
            msg = '%s\n%s'%(msg, "Error en fiscal_position_id %s"% vals['fiscal_position_id'])
       

        vals = {
            'name': vals['name'],
            'partner_id': partner_id,
            'partner_ref': vals['partner_ref'],
            'currency_id': vals['currency_id'], ## self.get_id_from_xml_id(vals['currency_id']),
            'date_order': vals['date_order'],
            'origin': vals['origin'],
            'state': states[vals['state']]
        }
        if global_analytic_id:
            vals['global_analytic_id'] = global_analytic_id
        if global_analytic_tag_id:
            vals['global_analytic_tag_id'] = global_analytic_tag_id
        if picking_type_id_:
            vals['picking_type_id_'] = picking_type_id_
        if payment_mode_id:
            vals['payment_mode_id'] = payment_mode_id

        if payment_term_id:
            vals['payment_term_id'] = payment_term_id
        if supplier_partner_bank_id:
            vals['supplier_partner_bank_id'] = supplier_partner_bank_id
        if fiscal_position_id:
            vals['fiscal_position_id'] = fiscal_position_id

        po = self.env['purchase.order'].new(vals)
        order_vals = po._convert_to_write(po._cache)
        new_po = self.env['purchase.order'].create(order_vals)
        po.message_post("Pedido de compra IMPORTADO. REVISAR")
        if msg:
            msg = "Error en PO %s\n%s"%(po.name, msg)
            self._logger_error(msg)
            new_po.message_post(msg)
        return new_po

    def create_line_from_row_vals(self, po, vals):
        product_id = self.env['product.product'].browse(vals['product_id'])
        if not product_id:
            self._logger_error("ERROR EN EL PO %s Producto %s"%(po.name, vals['product_id']))
            return False
        tax_ids = []
        for tax in vals['taxes_id'].split(','):
            if tax:
                t_id = self.get_id_from_xml_id(tax)
                if t_id:
                    tax_ids.append(self.get_id_from_xml_id(tax))
                else:
                    self._logger_error("ERROR EN EL PO %s Impuestos %s"%(po.name, tax))

        account_analytic_id = vals['account_analytic_id']
        if vals['account_analytic_id'] and not account_analytic_id:
            self._logger_error("ERROR EN EL PO %s Cuenta analitica "%po.name)
        line_vals = {
            'order_id': po.id,
            'product_id': vals['product_id'],
            'product_uom': vals['product_uom_id'],
            'name': vals['line.name'],
            'product_qty': vals['product_qty'],
            'price_unit': vals['price_unit'],
            'date_planned': vals['date_planned'],
            'discount': vals['discount'],
            'price_subtotal': vals['price_subtotal'],
        }
        if account_analytic_id:
            line_vals['account_analytic_id'] = account_analytic_id
        if tax_ids:
            line_vals['taxes_id'] =  [(6,0,tax_ids)]
        if vals['analytic_tag_ids']:
            line_vals['analytic_tag_ids'] =  [(6,0, [vals['analytic_tag_ids']])]

        order_line = self.env['purchase.order.line'].new(line_vals)
        order_line._compute_amount()
        order_line_vals = order_line._convert_to_write(order_line._cache)
        return po.order_line.create(order_line_vals)


    def _parse_row_vals(self, row, idx, row_vals):
        if str(row[1]):
            res = {
                'xml_id': str(row[0]),
                'name': str(row[1]),
                'partner_id': str(row[2]),
                'partner_ref': str(row[3]),
                'currency_id': int(row[4]),
                'date_order': str(row[5]),
                'origin': str(row[6]),
                'global_analytic_id': row[7] and int(row[7]),
                'global_analytic_tag_id': row[8] and int(row[8]),
                'picking_type_id_': row[9] and  int(row[9]),
                'payment_term_id': row[10] and int(row[10]),
                'payment_mode_id': row[11] and int(row[11]),
                'supplier_partner_bank_id': row[12] and int(row[12]),
                'fiscal_position_id': row[13] and int(row[13]),
                'date_aprove': str(row[14]),
                'state': str(row[15]),
            }
        else:
            res = row_vals

        if row[16]:
            res.update({
            'line_id': str(row[16]),
            'sequence2': int(row[17]),
            'product_id': row[18] and int(row[18]),
            'line.name': str(row[19]),
            'account_analytic_id': row[20] and int(row[20]),
            'analytic_tag_ids': row[21] and int(row[21]),
            'product_qty': float(row[22]),
            'product_uom_id': row[23] and int(row[23]),
            'price_unit': float(row[24]),
            'discount': float(row[25]),
            'sequence': row[26]*1,
            'taxes_id': str(row[27]),
            'price_subtotal': row[28] and float(row[28]) or 0.00,
            'date_planned': str(row[29]),

        })
        else:
             res.update({
            'line_id': '',
            'sequence2': 0,
            'product_id': '',
            'line.name': '',
            'account_analytic_id': '',
            'analytic_tag_ids': '',
            'product_qty': 0,
            'product_uom_id': '',
            'price_unit': 0.00 ,
            'discount': 0,
            'sequence': 0,
            'taxes_id': '',
            'price_subtotal': 0.00,
            'date_planned': str(row[14])
        })
        return res

    def get_id_from_xml_id(self, xml_id):
        #_logger.info(_('Buscando %s')%xml_id)
        try:
            if not xml_id:
                return False
            obj_id = self.env.ref(xml_id)
            #_logger.info(_(' ------- Se ha eoncontrado %s')%obj_id.display_name)
            return obj_id.id
        except:
            _logger.info(_(' ---------------------------------\n  No se ha eoncontrado %s\n --------------------------------')%xml_id)
            return False

    def get_from_xml_id(self, xml_id):
        return self.env.ref(xml_id)
    
    def action_view_purchases(self, purchase_ids):
        self.ensure_one()
        action = self.env.ref("purchase.purchase_rfq")
        action['domain'] = [('id', 'in', purchase_ids)]
        return action

    def import_purchases(self):
        test = False
        self.ensure_one()
        _logger.info(_('STARTING PRODUCT IMPORTATION'))
        # get the first worksheet
        file = base64.b64decode(self.file)
        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        created_product_ids = []
        idx = 1
        purchase_ids = self.env['purchase.order']
        po = self.env['purchase.order']
        row_vals={}
        for nline in range(1, sh.nrows):
            idx += 1
            row = sh.row_values(nline)

            row_vals = self._parse_row_vals(row, idx, row_vals)
            name = row_vals['name']

            if name and str(row[1]):
                po = self.env['purchase.order'].search([('name', '=', name)])
                if po:
                    _logger.info("La compra %s ya existe" % po.name)
                    ## po = self.env['purchase.order']
                    ### Para repetir
                    if test:
                        po.state = 'cancel'
                        po.unlink()
                        po = self.create_from_row_vals(row_vals)
                        purchase_ids |= po
                    else:
                        po = self.env['purchase.order']
                    continue                
                else:
                    _logger.info("------------- >>>> Creando %s:" % name)
                    po = self.create_from_row_vals(row_vals)
                    purchase_ids |= po
            if not po:
                continue
            if row_vals['line_id']:
                new_line = self.create_line_from_row_vals(po, row_vals)
        return self.action_view_purchases(purchase_ids.ids)

