# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# TODO  PLANTILLA:
# ref_template
# ref_template_color
# !!! estas dos columnas son clave y determinan product_template y PT.XXXXXX YYY cuando es posible
# marca - se crea como atributo y como caracteristica de atributo
# color general - amazon, hace falta una especie de "color general"
# composicion de colores - amazon separados por coma o / todos los colores que tiene, se pasa a atributos
# name - Auto explicativo NOT NULL
# categoria NOT NULL -- ver si la metemos a palo seco
# ATRIBUTOS - TODO preguntar a kiko cual era la lógica de esto, por que no recuerdo porque habia tipo y nombre
# Esto se duplicai en atributo y COMO atributo para facilitar el trabajo a los de front
# nombre de talla NOT NULL
# tipo de product - T-Shirt sandalias y eso
# <!-- Marca, puesto arriba -->
# Genero - Puede ser falso?
# edad - puede ser falso?
# DESCRIPCIONES
# descripcion corta
# descripcion larga
# ESPECIFICO por product_product
# coste NOT NULL
# precio de venta NOT NULL - Si es distinto para alguno cambiar
# valor de la talla - 46,47,etc NOT NULL
# supplier name - amazon, esto es un campo que vamos aprovechar para crear ls relaciones entre las tallas
# EAN NOT NULL
# Campos de longitud VARIABLE, pueden aparecer 30 y no son obligatorios
# Si el nombre del campo es tag se busca una etuiqueta
# si el nombre del campo es attribute, se busca un atributo
# TODO vista para ver errorres o devolver resultados

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import xlrd
import base64

import logging
_logger = logging.getLogger(__name__)

# Global variable to store the new created templates
template_ids = []


class ProductImportWzd(models.TransientModel):

    _name = 'product.import.wzd'

    name = fields.Char('Importation name', required=True)
    file = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Filename')

    brand_id = fields.Many2one('product.brand', 'Brand')
    categ_id = fields.Many2one('product.category', 'Default product category')

    @api.onchange('file')
    def onchange_filename(self):
        if not self.name and self.filename:
            self.name = self.filename and self.filename.split('.')[0]

    def _parse_row_vals(self, row, idx):
        res = {
            'warehouse_id': str(row[0]),
            'barcode': str(row[1]),
            'name': str(row[2]).replace('_',''),
            'product_id': str(row[3]).replace('_',''),
            'location_id': str(row[4]),
            'pathaway_id': str(row[5]),
        }
        # Check mandatory values setted
        return res

    def _create_xml_id(self, xml_id, res_id, model):

        virual_module_name = 'SL'
        self._cr.execute(
            'INSERT INTO ir_model_data (module, name, res_id, model) \
            VALUES (%s, %s, %s, %s)',
                        (virual_module_name, xml_id, res_id, model))



    def action_view_location(self, location_ids):
        self.ensure_one()
        action = self.env.ref(
            'stock.action_location_form').read()[0]
        action['domain'] = [('id', 'in', location_ids)]
        return action

    def import_products(self):
        """
            'warehouse_id': str(row[0]),
            'barcode': str(row[1]),
            'name': str(row[2]),
            'product_id': str(row[3]),
            'location_id': str(row[4]),
            'pathaway_id': str(row[5]),
        """
        ## import pdb; pdb.set_trace()
        self.ensure_one()
        _logger.info(_('STARTING LOCATION IMPORTATION'))
        # get the first worksheet
        file = base64.b64decode(self.file)
        book = xlrd.open_workbook(file_contents=file)
        sh = book.sheet_by_index(0)
        created_product_ids = []
        idx = 1
        error = []
        location_ids = self.env['stock.location']
        SL = self.env['stock.location']
        for nline in range(1, sh.nrows):
            idx += 1
            row = sh.row_values(nline)
            row_vals = self._parse_row_vals(row, idx)
            if not row_vals['product_id'] and not row_vals['name']:
                raise UserError ("No se ha encontrado una ubicación padre")
                break
            if row_vals['location_id']:
                domain = [('barcode', '=', row_vals['location_id'])]
                new_location_id = SL.search(domain)
                if new_location_id:
                    parent_location_id = new_location_id
            if row_vals['pathaway_id']:
                domain = [('name', '=', row_vals['pathaway_id'])]
                putaway_id = self.env['product.putaway'].search(domain)
            if not parent_location_id:
                raise UserError ("No se ha encontrado una ubicación padre")
            if not putaway_id:
                raise UserError ("No se ha encontrado un putaway %s" % row_vals['pathaway_id'])
            product_id = self.env['product.product'].search([('default_code', '=', row_vals['product_id'])], limit = 1)
            if not product_id:
                err = 'No se ha encontrado el codigo %s' %row_vals['product_id']
                _logger.info(err)
                error += [err]
            location_id = SL.search([('barcode', '=', row_vals['barcode'])])
            if not location_id:
                new_slvals = {
                    'name': row_vals['name'], 
                    'barcode': row_vals['barcode'],
                    'usage': 'internal',
                    'location_id': parent_location_id.id}
                location_id = SL.create(new_slvals)
            if not product_id:
                continue
            location_ids += location_id
            new_putaway_vals = {
                'putaway_id': putaway_id.id,
                'product_tmpl_id': product_id.product_tmpl_id.id,
                'fixed_location_id': location_id.id
            }
            self.env['stock.product.putaway.strategy'].create(new_putaway_vals)
            _logger.info(_('IMPORTED PRODUCT %s / %s') % (idx, sh.nrows - 1))
        if error:
            for err in error:
                _logger.info("Error: %s" %err)
        ## raise UserError ("NO importar")
        return self.action_view_location(created_product_ids)
