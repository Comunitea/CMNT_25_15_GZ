# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2015 Comunitea Servicios Tecnológicos S.L.
#                       Omar Castiñeira Saavedra <omar@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api
from lxml import etree


class CreateFacturae(models.TransientModel):

    _inherit = "create.facturae"

    @api.multi
    def end_document_hook(self, xml_facturae):
        res = super(CreateFacturae, self).end_document_hook(xml_facturae)
        doc = etree.XML(res)
        invoice_id = self.env.context.get('active_ids', [])[0]
        inv_obj = self.env["account.invoice"]
        inv_line_obj = self.env["account.invoice.line"]
        invoice = inv_obj.browse(invoice_id)
        lines = doc.xpath("//InvoiceLine")
        visited_line = []
        for line in lines:
            cont = 0
            if invoice.num_contract:
                elem0 = etree.Element('ReceiverContractReference')
                elem0.text = invoice.num_contract
                line.insert(cont, elem0)
                cont += 1
                elem1 = etree.Element('ReceiverTransactionReference')
                elem1.text = invoice.num_contract
                line.insert(cont, elem1)
                cont += 1
            inv_line = False
            for child in line.getchildren():
                if child.tag == "ItemDescription":
                    description = child.text
                elif child.tag == "Quantity":
                    qty = float(child.text)
                elif child.tag == "UnitPriceWithoutTax":
                    price_unit = float(child.text)

            inv_line = inv_line_obj.search([('invoice_id' , '=', invoice.id),
                                            ("name", '=', description),
                                            ('price_unit', '=', price_unit),
                                            ('quantity', '=', qty),
                                            ('id', 'not in', visited_line)])
            if inv_line and inv_line[0].picking_id:
                visited_line.append(inv_line[0].id)
                elem2 = etree.Element('DeliveryNotesReferences')
                elem3 = etree.Element('DeliveryNote')
                elem4 = etree.Element('DeliveryNoteNumber')
                elem4.text = inv_line[0].picking_id.name
                elem3.insert(0, elem4)
                elem5 = etree.Element('DeliveryNoteDate')
                elem5.text = inv_line[0].picking_id.date[:10]
                elem3.insert(1, elem5)

                elem2.insert(0, elem3)
                line.insert(cont, elem2)

        res = etree.tostring(doc)
        return res
