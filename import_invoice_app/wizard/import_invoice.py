# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, exceptions, api, _
import io
import tempfile
import binascii
import logging
from datetime import datetime, timedelta

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
# for xls 
try:
	import xlrd
except ImportError:
	_logger.debug('Cannot `import xlrd`.')


from odoo import api, fields, models, _

class Stock_Import(models.TransientModel):
	_name = 'import.invoice'
	_description = 'Import Invoice'

	invoice_line_account = fields.Selection([('product','Use From Product'),('file','Use From File')],string="Invoice Line Account",default='product')
	file_seq = fields.Selection([('default','Use Default Sequence'),('file','Use Sequence From File')],string='Sequence Option ',default='default')
	customer_option = fields.Selection([('name', 'Name'),('ref', 'Internal Reference '),('external','External ID')],string='Search Customer ',default='ref')
	invoice_option = fields.Selection([('customer', 'Customer Invoice'),('vendor', 'Vendor Bill'),('cus_refund','Customer Refund'),('ven_refund','Vendor Refund')],string='Invoice Option ',default='customer')
	import_prod_option = fields.Selection([('name', 'Name'),('barcode', 'Barcode'),('ref', 'Internal Reference '),('external','External ID')],string='Search Product',default='name')
	file_type = fields.Selection([('csv','CSV'),('xls','XLS')],default='xls',string="Type",required=True)
	import_file = fields.Binary('Select File',required=True)

	def import_file_button(self):
		if self.invoice_option == 'customer':
			type_invoice = 'out_invoice'

		if self.invoice_option == 'vendor':
			type_invoice = 'in_invoice'

		if self.invoice_option == 'cus_refund':
			type_invoice = 'out_refund'

		if self.invoice_option == 'ven_refund':
			type_invoice = 'in_refund'
		flag = False
		validate_res = self.env['import.validation'].create({'name' : 'validate'})
		invoice_obj = self.env['account.move']
		account_obj = self.env['account.account']
		invoice_line_obj = self.env['account.move.line']
		company_id = self.env['res.users'].browse(self._context.get('uid')).company_id
		if self.file_type == 'xls' :
			
			fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
			fp.write(binascii.a2b_base64(self.import_file))
			fp.seek(0)
			values = {}
			invoice_ids_lst = []
			try:
				workbook = xlrd.open_workbook(fp.name)
			except Exception:
				raise exceptions.UserError(_("Invalid file!"))
			sheet = workbook.sheet_by_index(0)
			sheet = workbook.sheet_by_index(0)
			warning = False
			product = self.env['product.product']
			for no in range(sheet.nrows):
				if no <= 0:
					fields = map(lambda row:row.value.encode('utf-8'), sheet.row(no))
				else :
					data = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(no)))

					for i in range (0, 19):
						try:
							d = data[i]
						except IndexError:
							raise ValidationError(_('No existe la columna "%s". Revise que la estructura del archivo tenga 19 columnas') % (i+1,))

					values.update({'invoice':data[0],'customer':data[1],'delivery':data[2],'payment':data[3],'date':data[4],
								'sales_person':data[5],'sales_team':data[6],'journal' : data[7],'fiscal_potion':data[8],'product':data[9],
								'description':data[10],'account':data[11],'qty':data[12],
								'uom':data[13],'price':data[14],'tax':data[15],'analytic_account':data[16],'analytic_tags':data[17],'invoice_date_due':data[18]})

					if data :
						partner_res = False
						if self.customer_option == 'name':
							partner_res = self.env['res.partner'].search([('name','=',values['customer'])],limit=1)
						if self.customer_option == 'ref':
							partner_res = self.env['res.partner'].search([('ref','=',values['customer'])],limit=1)
						if self.customer_option == 'external':
							try :
								partner_res = self.env.ref(values['customer'])
							except :
								raise ValidationError(_('"%s" is not an external id.')%(values['customer']))
						if not partner_res :
							raise ValidationError(_('"%s" is not available.')%(values['customer']))


						#Cambia temporalmente la cxc y cxp
						account_payable_id = partner_res.property_account_payable_id
						account_receivable_id = partner_res.property_account_receivable_id

						account_file = account_obj.search([('code','=',values['account'])], limit=1)
						if account_file:
						   if self.invoice_option == 'customer':
						      partner_res.property_account_receivable_id = account_file[0]

						   if self.invoice_option == 'vendor':
						      partner_res.property_account_payable_id = account_file[0]

						journal_res = False
						journal_res = self.env['account.journal'].search([('name','=',values['journal'])],limit=1)
						if not journal_res :
							raise ValidationError(_('"%s" journal is not available.')%(values['journal']))

						payment_res = False
						payment_res = self.env['account.payment.term'].search([('name','=',values['payment'])],limit=1)
						if not payment_res :
							raise ValidationError(_('"%s" payment term is not available.')%(values['payment']))

						DATETIME_FORMAT = '%d/%m/%Y'
						if isinstance(values['date'], str):
							value_date = datetime.strptime(values['date'], DATETIME_FORMAT).date()
							invoic_date = value_date
						else:
							value_date_int = int(float(values['date']))
							a1_as_datetime = datetime(*xlrd.xldate_as_tuple(value_date_int, workbook.datemode))
							invoic_date = a1_as_datetime.date().strftime(DATETIME_FORMAT)

						#fecha de vencimiento
						if values.get('invoice_date_due'):
						   if isinstance(values['invoice_date_due'], str):
							   value_date = datetime.strptime(values['invoice_date_due'], DATETIME_FORMAT).date()
							   invoice_date_due = value_date
						   else:
							   value_date_int = int(float(values['invoice_date_due']))
							   a1_as_datetime = datetime(*xlrd.xldate_as_tuple(value_date_int, workbook.datemode))
							   invoice_date_due = a1_as_datetime.date().strftime(DATETIME_FORMAT)

						sales_person_res = False
						sales_team_res = False
						fiscal_potion_res =False
						if values.get('sales_person') :
							sales_person_res = self.env['res.users'].search([('name','=',values['sales_person'])],limit=1)
							if not sales_person_res :
								raise ValidationError(_('"%s" sales person is not available.')%(values['sales_person']))

						if values.get('sales_team') :
							sales_team_res = self.env['crm.team'].search([('name','=',values['sales_team'])], limit=1)
							if not sales_team_res :
								raise ValidationError(_('"%s" sales team is not available.')%(values['sales_team']))

						if values.get('fiscal_potion') :
							fiscal_potion_res = self.env['account.fiscal.position'].search([('name','=',values['fiscal_potion'])], limit=1)
							if not fiscal_potion_res :
								raise ValidationError(_('"%s" fiscal position is not available.')%(values['fiscal_potion']))

						invoice_res = False
						product_rec = False

						if self.import_prod_option == 'name' :
							product_rec = product.search([('name', '=',values['product'])],limit=1)
							if not product_rec :
								raise ValidationError(_('"%s" Product is not available.')%(values['product']))

						if self.import_prod_option == 'barcode':
							product_rec = product.search([('barcode', '=',values['product'])],limit=1)
							if not product_rec :
								raise ValidationError(_('"%s" Product is not available for this barcode.')%(values['product']))

						if self.import_prod_option == 'ref':
							product_rec = product.search([('default_code', '=',values['product'])],limit=1)
							if not product_rec :
								raise ValidationError(_('"%s" Product is not available for this internal reference  .')%(values['product']))

						if self.import_prod_option == 'external':
							try:
								product_rec = self.env.ref(values['product'])
							except :
								raise  UserError(_('"%s" Product is not available for this external id.')%(values['product']))

						account_product = False
						account_partner = False
						if self.invoice_option == 'customer':
							account_product = product_rec.property_account_income_id or product_rec.categ_id.property_account_income_categ_id
							account_partner = partner_res.property_account_receivable_id

						if self.invoice_option == 'vendor':
							account_product = product_rec.property_account_expense_id or product_rec.categ_id.property_account_expense_categ_id
							account_partner = partner_res.property_account_payable_id

						if self.invoice_option == 'cus_refund':
							account_product = product_rec.property_account_income_id or product_rec.categ_id.property_account_income_categ_id
							account_partner = partner_res.property_account_receivable_id

						if self.invoice_option == 'ven_refund':
							account_product = product_rec.property_account_expense_id or product_rec.categ_id.property_account_expense_categ_id
							account_partner = partner_res.property_account_payable_id

						if self.invoice_line_account == 'product':
							account_res = account_product
						else:
							# se toma la cuenta de la línea
							account_res = account_obj.search([('code','=',values['account'])], limit=1)
							if not account_res :
								raise ValidationError(_('"%s" Account is not available .') % (values['account']))

							#La cuenta de la línea no puede ser la misma que la del tercero, porque sino no crea línea de factura
							if account_res.id == account_partner.id:
								raise ValidationError(_('La cuenta "%s" de la línea no puede ser la misma cuenta por cobrar/pagar parametrizada en el contacto "%s"') % (values['account'], partner_res.name))

						uom_rec = self.env['uom.uom'].search([('name','=',values['uom'])],limit=1)
						if not uom_rec :
							raise ValidationError(_('"%s" Uom is not available.')%(values['uom']))
						
						tags_list = []

						analytic_account_res = self.env['account.analytic.account'].search([('code','=',values['analytic_account'])], limit=1)
						if not analytic_account_res :
								raise ValidationError(_('"%s" Analytic Account is not available .')%(values['analytic_account']))

						tags_list = []
						if values.get('analytic_tags') :
							if ';' in  values.get('analytic_tags'):
								tag_names = values.get('analytic_tags').split(';')
								for name in tag_names:
									tag= self.env['account.analytic.tag'].search([('name', '=', name)], limit=1)
									if not tag:
										raise ValidationError(_('"%s" Tag not in your system') % name)
									tags_list.append(tag.id)

							elif ',' in  values.get('analytic_tags'):
								tag_names = values.get('analytic_tags').split(',')
								for name in tag_names:
									tag= self.env['account.analytic.tag'].search([('name', '=', name)], limit=1)
									if not tag:
										raise ValidationError(_('"%s" Tag not in your system') % name)
									tags_list.append(tag.id)
							else:
								tag_names = values.get('analytic_tags').split(',')
								for name in tag_names:
									tag= self.env['account.analytic.tag'].search([('name', '=', name)], limit=1)
									if not tag:
										raise ValidationError(_('"%s" Tag not in your system') % name)
									tags_list.append(tag.id)

						tax_list = []
						if values.get('tax'):
							if ';' in  values.get('tax'):
								tax_names = values.get('tax').split(';')
								for name in tax_names:
									tax= self.env['account.tax'].search([('name', '=', name)], limit=1)
									if not tax:
										raise ValidationError(_('"%s" Tax not in your system') % name)
									
									tax_list.append(tax.id)

							elif ',' in  values.get('tax'):
								tax_names = values.get('tax').split(',')
								for name in tax_names:
									tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')], limit=1)
									if not tax:
										raise ValidationError(_('"%s" Tax not in your system') % name)
									
									tax_list.append(tax.id)

							else:
								tax_names = values.get('tax').split(',')
								for name in tax_names:
									tax= self.env['account.tax'].search([('name', '=', name),('type_tax_use','=','sale')], limit=1)
									if not tax:
										raise ValidationError(_('"%s" Tax not in your system') % name)
									
									tax_list.append(tax.id)

						if sales_person_res :
							sales_person_id = sales_person_res.id
						else :
							sales_person_id = False

						if sales_team_res :
							sales_team_id = sales_team_res.id
						else :
							sales_team_id = False

						if fiscal_potion_res :
							fiscal_potion_id = fiscal_potion_res.id
						else :
							fiscal_potion_id = False

						finance_list = {'date_maturity': invoice_date_due, 'amount': float(values.get('price'))}

						line_vals = {	'product_id' : product_rec.id,
										'quantity' : values.get('qty'),
										'price_unit' : values.get('price'),
										'name' : values.get('description'),
										'account_id' : account_res.id,
										'product_uom_id' : uom_rec.id,
										'analytic_account_id':analytic_account_res.id ,
										'analytic_tag_ids':([(6,0,tags_list)]),
										'tax_ids':([(6,0,tax_list)]),
						}

						new_invoice_ids = invoice_obj.create({
										'partner_id':partner_res.id,
										'move_type':type_invoice,
										'journal_id' :journal_res.id,
										#'partner_shipping_id' : delivery_res.id,
										'invoice_payment_term_id':payment_res.id,
										'invoice_date':invoic_date,
										'user_id':sales_person_id ,
										'team_id':sales_team_id,
										'fiscal_position_id':fiscal_potion_id,
										'import_seq': (self.file_seq == 'file'),
										'name': values['invoice'],
										'invoice_line_ids' : [(0,0,line_vals)],
										#'line_ids_financing' : [(0,0,finance_list)],
						})
						invoice_ids_lst.append(new_invoice_ids.id)
								
			if invoice_ids_lst:
				invoice_ids_lst = list(set(invoice_ids_lst))
				invoice_ids = invoice_obj.browse(invoice_ids_lst)
				invoice_ids.write({'state':'draft'})

				#Cambia temporalmente la cxc y cxp
				partner_res.property_account_payable_id = account_payable_id 
				partner_res.property_account_receivable_id = account_receivable_id
		
		if flag == True :
			return {
							'view_mode': 'form',
							'res_id': validate_res.id,
							'res_model': 'import.validation',
							'view_type': 'form',
							'type': 'ir.actions.act_window',
							'target':'new'
					}