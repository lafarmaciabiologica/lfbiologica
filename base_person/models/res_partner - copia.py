# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
# Copyright (c) 2017 Innovatecsa S.A.S. (http://www.innovatecsa.com).
#
##############################################################################

from odoo import api, fields, models, tools, _


class ResPartner(models.Model): 
    _inherit = 'res.partner'
    
    def generate_dv_co(self, ref):

        print('ref------------------',ref)
    
        if not vat or not ref:
            return False

        if type(ref) == str:
            ref = ref.replace('-','',1).replace('.','',2)

        if len(str(ref)) < 4:
            return False		
        try:
            int(ref)
        except ValueError:
            return False
		
        nums = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        sum = 0
        RUTLen = len(str(ref))
	
        for i in range (RUTLen - 1, -1, -1):
            sum += int(str(ref)[i]) * nums [RUTLen - 1 - i]
		
        if sum % 11 > 1:
            return str(11 - (sum % 11))
        else:
            return str(sum % 11)
    
    #@api.multi
    def _check_digito_verificacion(self):
        print('partner+++++++++++++++++++++++++++++ ',partner.ref)
        for partner in self:
          if ((not partner.ref) and (not partner.dv)) or ((not partner.is_company) and (not partner.dv)):
              return True
  
          dv = self.generate_dv_co(partner.ref)
          if dv != partner.dv:
              return False
          else:
              return True
           
    #@api.multi       
    def _check_solo_digitos(self):
        print('partner 1',partner.ref)
        for partner in self:
          if partner.dv:    
              return partner.dv.isdigit()
           
          if partner.ref:    
              return partner.ref.isdigit()
            
        return True
    
    @api.model
    def _check_dv(self):
    
        partner_obj = self
	      
        print('partner_obj ******************', partner_obj)

        if partner_obj.is_company and not partner_obj.dv:    
            return False

        return True


    first_name = fields.Char('Primer nombre', size=32)
    middle_name = fields.Char('Segundo nombre', size=32)
    surname = fields.Char('Primer apellido', size=32)
    mother_name = fields.Char("Segundo apellido", size=32)    
    comercial_name = fields.Char('Nombre comercial', size=128, required=False, index=True)
    dv = fields.Char('DV', size=1, index=True, help='Dígito de verificación')
    type_ident_id = fields.Many2one('l10n_latam.identification.type', string='Tipo de identificacion')
                
    _sql_constraints = [('vat_uniq', 'unique(vat, company_id)', 'La identificacion tributaria debe ser unica. El numero ingresado ya existe'),
                        ('ref_uniq', 'unique(ref, company_id)', 'La identificacion debe ser unica. El numero ingresado ya existe'),
                        ('name_uniq', 'unique(name, company_id)', 'El nombre debe ser unico. El nombre o razon social ingresado ya existe')
                       ]
                       		    
    _constraints = [
            (_check_solo_digitos, 'Error!\nEl campo referencia interna y dígito de verificación aceptan solo números. Revise si tiene espacios en blanco', ['ref','dv']),
            (_check_dv, 'Error!\nSi es persona jurídica requiere el dígito de verificación.', ['dv']),
            (_check_digito_verificacion, 'Error!\nEl dígito de verificación no coinciden con el número ingresado.', ['ref','dv']),
    ]

    @api.onchange('first_name', 'middle_name', 'surname', 'mother_name')
    def onchange_person_name(self):
        if not self.is_company:
            self.name = (self.first_name and (self.first_name+' ') or '') + (self.middle_name and (self.middle_name+' ') or '') + (self.surname and (self.surname+' ') or '') + (self.mother_name and (self.mother_name+' ') or '')



