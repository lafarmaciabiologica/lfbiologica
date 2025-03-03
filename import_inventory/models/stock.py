# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, exceptions, api, _
import io
import tempfile
import binascii
import logging
_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class gen_inv_2(models.Model):
    _name = "generate.inv"
    _description = 'Generar inventario'

    product_counter_main = fields.Integer("Counter")

    @api.model
    def default_get(self, fields):
        res = super(gen_inv_2, self).default_get(fields)
        inv_id = self.env['generate.inv'].sudo().search([],order="id desc",limit=1)
        if inv_id:
            res.update({
                'product_counter_main' : inv_id.product_counter_main
                })
        else:
            res.update({
                'product_counter_main' : ''
                })
        return res

class gen_inv(models.TransientModel):
    _name = "gen.inv"
    _description = 'Generar inventario'

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='xls')
    import_prod_option = fields.Selection([('barcode', 'Barcode'),('code', 'Code'),('name', 'Name')],string='Import Product By ',default='code')
    is_validate_inventory = fields.Boolean(string="Validate Inventory", required=True, default=True)

    
    def import_csv(self):

        """Load Inventory data from the CSV file."""
        if not self.file:
            raise ValidationError(_('Please Select File'))
        if self.import_option == 'csv':
            
            data = base64.b64decode(self.file)
            try:
                file_input = io.StringIO(data.decode("utf-8"))
            except UnicodeError:
                raise ValidationError('Invalid file!')

            """Load Inventory data from the CSV file."""
            ctx = self._context
            keys=['code', 'quantity','location','cost']
            stloc_obj = self.env['stock.location']
            inventory_obj = self.env['stock.quant']
            product_obj = self.env['product.product']
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            flag = 0

            generate_inv = self.env['generate.inv']
            counter_product = 0.0

            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.ValidationError(_("Invalid file!"))
            values = {}

            
            for i in range(len(file_reader)):
                if i!= 0:
                    val = {}
                    try:
                         field = list(map(str, file_reader[i]))
                    except ValueError:
                         raise exceptions.ValidationError(_("Dont Use Charecter only use numbers"))
                    
                    values = dict(zip(keys, field))
                    
                    if self.import_prod_option == 'barcode':
                        prod_lst = product_obj.search([('barcode',  '=',values['code'])]) 
                    elif self.import_prod_option == 'code':
                        prod_lst = product_obj.search([('default_code',  '=',values['code'])]) 
                    else:
                        prod_lst = product_obj.search([('name', '=',
                                                    values['code'])])
                    if not values.get('location'):
                        raise ValidationError(_("Please fill 'LOCATION' column in CSV or XLS file."))
                    stock_location_id = self.env['stock.location'].search([('name','=',values['location'])])
                    if not stock_location_id:
                        raise ValidationError(_('"%s" Location is not available.')%(values['location']))
     
                    if prod_lst:
                        val['product'] = prod_lst[0].id
                        val['quantity'] = values['quantity']

                    if bool(val):
                        product_id = product_obj.browse(val['product'])
                        product_uom_id=product_obj.browse(val['product']).uom_id

                        search_line = self.env['stock.quant'].search([('product_id','=',val['product']),('location_id','=',stock_location_id.id)])
                        if search_line :
                            for stock_line_id in search_line :
                                stock_line_id.write({'inventory_quantity' : val['quantity']})
                                stock_line_id._compute_inventory_diff_quantity()
                                if self.is_validate_inventory == True:
                                    stock_line_id.action_apply_inventory()

                        else :

                            stock_line_id = inventory_obj.create({'product_id':val['product'] ,'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'inventory_quantity': val['quantity']})
                            stock_line_id._compute_inventory_diff_quantity()
                            if self.is_validate_inventory == True:
                                stock_line_id.action_apply_inventory()
                        
                        flag =1
                        for i in prod_lst:
                            counter_product += 1
                        g_inv_id = generate_inv.sudo().create({
                            'product_counter_main' : int(counter_product)
                        })

                    else:
                        raise ValidationError(_('Product Not Found  "%s"') % values.get('code'))

            if flag ==1:
                return  {
                        'name': _('Success'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'generate.inv',
                        'view_id': self.env.ref('import_inventory.success_import_wizard').id,
                        'type': 'ir.actions.act_window',
                        'target': 'new'
                        }
            else:
                return True 

        else:
            # IMPORT EXCEL

            try:
                fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                values = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except Exception:
                raise exceptions.ValidationError(_("Invalid file!"))
            product_obj = self.env['product.product']
            
            inventory_obj = self.env['stock.quant']

            flag = 0
            generate_inv = self.env['generate.inv']
            counter_product = 0.0

            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
                else:
                    line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                    if line:
                        if len(line) > 2:
                            values.update({'code':line[0],'quantity':line[1],'line_location_id':line[2],'cost':line[3],'lot':line[4]})
                        else:
                            raise ValidationError(_("Please fill 'LOCATION' column in CSV or XLS file."))
                        if self.import_prod_option == 'barcode':
                            prod_lst = product_obj.search([('barcode',  '=',values['code'])]) 
                        elif self.import_prod_option == 'code':
                            code = str(values.get('code'))
                            if code.find('.') != -1:
                               code = code[:code.find('.')]
                            prod_lst = product_obj.search([('default_code',  '=',code)]) 
                        else:
                            prod_lst = product_obj.search([('name', '=',
                                                    values['code'])])
                        stock_location_id = self.env['stock.location'].search([('complete_name','=',values['line_location_id'])])
                        if not stock_location_id:
                            raise ValidationError(_('"%s" Location is not available.')%(values['line_location_id']))

                        #valida no ingresar cantidad ni costo negativo
                        cost = values.get('cost')
                        if cost:
                           cost_value = float(cost)
                           if cost_value <= 0:
                              raise ValidationError(_('El costo no puede ser cero ni negativo en el producto "%s"')%(values['code']))

                        if prod_lst:
                            val['product'] = prod_lst[0].id
                            val['quantity'] = values['quantity']

                        if bool(val):
                            product_id = product_obj.browse(val['product'])
                            product_uom_id=product_obj.browse(val['product']).uom_id
                        
                            lot = str(values.get('lot'))
                            if lot.find('.') != -1:
                               lot = lot[:lot.find('.')]

                            lot_id = False
                            if lot:
                               lot_id = self.env['stock.lot'].search([('name','=',lot),('product_id','=',product_id.id)])
                               if not lot_id:
                                  raise ValidationError(_('El producto [%s]%s con serie/lote %s no existe')%(product_id.default_code or '', product_id.name, lot))

                               if product_id.tracking == 'none':
                                  raise ValidationError(_('El producto [%s]%s no esta configirado con seguimiento serie/lote')%(product_id.default_code or '', product_id.name))


                            if product_id.categ_id.property_cost_method != 'average':
                               raise ValidationError(_('El producto "%s" no está configurado con método Coste promedio')%(values['code']))

                            if product_id.categ_id.property_valuation != 'real_time':
                               raise ValidationError(_('El producto "%s" no está configurado con valuación del inventario Automatizado')%(values['code']))

                            if product_id.detailed_type != 'product':
                               raise ValidationError(_('El producto "%s" no está configurado como almacenable')%(values['code']))

                            if product_id.purchase_ok and product_id.purchase_method != 'receive':
                               raise ValidationError(_('El producto "%s" no está configurado con Política de control por Cantidades recibidas')%(values['code']))

                            if product_id.sale_ok and product_id.invoice_policy != 'delivery':
                               raise ValidationError(_('El producto "%s" no está configurado con Política de facturación por Cantidades entregadas')%(values['code']))


                            if cost:
                               product_id.standard_price = cost_value
                            
                            if lot_id:
                               lote = lot_id.id
                            else:
                               lote = False

                            search_line = self.env['stock.quant'].search([('product_id','=',val['product']),('location_id','=',stock_location_id.id),('lot_id','=',lote)])
                            if search_line :
                               for stock_line_id in search_line :
                                   stock_line_id.write({'inventory_quantity' : val['quantity']})
                                   stock_line_id._compute_inventory_diff_quantity()
                                   if self.is_validate_inventory == True:
                                      stock_line_id.action_apply_inventory()

                            else :

                                stock_line_id = inventory_obj.create({'product_id':val['product'] ,'location_id' : stock_location_id.id, 'product_uom_id' : product_uom_id.id  ,'inventory_quantity': val['quantity'], 'lot_id' : lote})
                                stock_line_id._compute_inventory_diff_quantity()
                                if self.is_validate_inventory == True:
                                    stock_line_id.action_apply_inventory()

                            flag =1
                            for i in prod_lst:
                                counter_product += 1
                            g_inv_id = generate_inv.sudo().create({
                                'product_counter_main' : int(counter_product)
                            })

                        else:
                            raise ValidationError(_('Product Not Found  "%s"') % values.get('code'))



            if flag ==1:
                return  {
                        'name': _('Success'),
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'generate.inv',
                        'view_id': self.env.ref('import_inventory.success_import_wizard').id,
                        'type': 'ir.actions.act_window',
                        'target': 'new'
                        }
            else:
                return True
            
