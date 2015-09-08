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

from openerp import _, tools
from openerp.osv import orm, fields
from edi_logging import logger
from mako.template import Template
from mako.lookup import TemplateLookup
import os
import time
log = logger("export_edi")

class edi_export(orm.TransientModel):

    _name = "edi.export"
    _columns = {
        'configuration': fields.many2one('edi.configuration','Configuración',required=True),
    }
    def default_get(self, cr, uid, fields, context=None):
        res = super(edi_export, self).default_get(cr, uid, fields, context=context)

        conf_ids = self.pool.get('edi.configuration').search(cr,uid,[])
        if not conf_ids:
            raise orm.except_orm(_('Error'), _('No existen configuraciones EDI.'))

        res.update({'configuration': conf_ids[0]})
        return res

    def create_doc(self,cr,uid,ids,obj,file_name,context):
        if obj:
            name=gln_e=gln_v=gln_c=gln_r=doc_type=sale_order_id=picking_id=invoice_id=False

            if context['active_model'] == u'sale.order':
                name = obj.name.replace(' ','').replace('.','')
                gln_e = obj.partner_order_id.gln
                gln_v = obj.company_id.partner_id.gln
                gln_c = obj.partner_invoice_id.gln
                gln_r = obj.partner_shipping_id.gln
                doc_type = 'ordrsp'
                sale_order_id = obj.id
                mode = obj.order_type
            elif context['active_model'] == u'stock.picking':
                name = obj.name.replace('/','')
                gln_e = obj.company_id.partner_id.gln
                gln_v = obj.company_id.partner_id.gln
                gln_c = obj.address_id.partner_id.gln
                gln_r = obj.address_id.partner_id.gln
                doc_type = 'desadv'
                picking_id = obj.id
                mode = '3'
            elif context['active_model'] == u'account.invoice':
                name = obj.name.replace('/','')
                gln_e = obj.company_id.partner_id.gln
                gln_v = obj.company_id.partner_id.gln
                gln_c = obj.address_invoice_id.gln
                gln_r = obj.address_invoice_id.gln
                doc_type = 'invoic'
                invoice_id = obj.id
                mode = obj.gi_cab_funcion
            else:
                raise orm.except_orm(_('Error'), _('El modelo no es ni un pedido ni un albarán ni una factura.'))

            if not self.pool.get('edi.doc').search(cr,uid,[('name','=',name)]) or context['active_model'] == u'account.invoice':
                f = open(file_name)
                values = {
                    'name' : name,
                    'file_name' : file_name.split('/')[-1],
                    'status': 'export',
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_process': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'mode' : mode,
                    'type': doc_type,
                    'sale_order_id': sale_order_id,
                    'picking_id' : picking_id,
                    'invoice_id' : invoice_id,
                    'gln_e':gln_e,
                    'gln_v':gln_v,
                    'gln_c':gln_c,
                    'gln_r':gln_r,
                    'message':f.read(),
                }
                f.close()
                file_id = self.pool.get('edi.doc').create(cr,uid,values)
                log.info(u"Exportado %s " % file_name)
            else:
                log.info(u"Ignorado %s, ya existe en el sistema." % file_name)
                raise orm.except_orm(_('Error'), _('El documento ya ha sido exportado con anterioridad.'))

        return file_id

    def addons_path(self,cr,uid,ids, path=False):
        if path:
            report_module = path.split(os.path.sep)[0]
            for addons_path in tools.config['addons_path'].split(','):
                if os.path.lexists(addons_path+os.path.sep+report_module):
                    return os.path.normpath( addons_path+os.path.sep+path )

        return os.path.dirname( self.path() )

    def export_files(self,cr,uid,ids,context=None):
        wizard = self.browse(cr,uid,ids[0])
        path = wizard.configuration.ftpbox_path + "/out"
        templates_path = wizard.addons_path('gauzon_edi')+os.sep+'wizard'+os.sep+'templates'+os.sep
        tmp_name = ''

        for obj in self.pool.get(context['active_model']).browse(cr,uid,context['active_ids']):
            if context['active_model'] == u'sale.order':
                tmp_name = '/order_template.xml'
                file_name = '%s%sORDRSP_%s.xml' % (path,os.sep,obj.name.replace(' ','').replace('.',''))
            elif context['active_model'] == u'stock.picking':
                tmp_name = '/picking_template.xml'
                file_name = '%s%sDESADV_%s.xml' % (path,os.sep,obj.name.replace('/',''))
            elif context['active_model'] == u'account.invoice':
                tmp_name = '/invoice_template.xml'
                file_name = '%s%sINVOIC_%s.xml' % (path,os.sep,obj.name.replace('/',''))

            mylookup = TemplateLookup( input_encoding='utf-8', output_encoding='utf-8', encoding_errors='replace')
            tmp = Template(filename=templates_path+tmp_name, lookup=mylookup, default_filters=['decode.utf8'])
            doc = tmp.render_unicode(o=obj).encode('utf-8','replace')
            f = file(file_name,'w'); f.write(doc);f.close()
            wizard.create_doc(obj,file_name,context)
            data_pool = self.pool.get('ir.model.data')
            action_model,action_id = data_pool.get_object_reference(cr, uid, 'gauzon_edi', "act_edi_doc")
            action = self.pool.get(action_model).read(cr,uid,action_id,context=context)

        return action

