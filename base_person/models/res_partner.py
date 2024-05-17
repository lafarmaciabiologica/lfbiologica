# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
# Copyright (c) 2017 Innovatecsa S.A.S. (http://www.innovatecsa.com).
#
##############################################################################

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = "Contactos"

    
    first_name = fields.Char('Primer nombre', size=32)
    middle_name = fields.Char('Segundo nombre', size=32)
    surname = fields.Char('Primer apellido', size=32)
    mother_name = fields.Char("Segundo apellido", size=32)    
    comercial_name = fields.Char('Nombre comercial', size=128, required=False, index=True)
    dv = fields.Char('DV', size=1, index=True, help='Dígito de verificación')
    is_nit = fields.Boolean(compute='_is_nit')

    _sql_constraints = [
                        ('vat_uniq', 'unique(vat, company_id)', 'La identificacion debe ser unica. El numero ingresado ya existe'),
                        ('ref_uniq', 'unique(ref, company_id)', 'El numero de identificacion debe ser unica. La numero ingresado ya existe'),
                        ('name_uniq', 'unique(name, company_id)', 'El nombre debe ser unico. El nombre o razon social ingresado ya existe')
                       ]                    
    @api.depends('l10n_latam_identification_type_id')
    def _is_nit(self):
        for rec in self:
           self.is_nit = self.env['l10n_latam.identification.type'].search([('id','=',self.l10n_latam_identification_type_id.id)]).is_vat
                
    @api.onchange('first_name', 'middle_name', 'surname', 'mother_name')
    def onchange_person_name(self):
        if not self.is_company:
           self.name = (self.first_name and (self.first_name+' ') or '') + (self.middle_name and (self.middle_name+' ') or '') + (self.surname and (self.surname+' ') or '') + (self.mother_name and (self.mother_name+' ') or '')

    @api.model_create_multi
    def create(self, vals_list):
        for record in vals_list:
            l10n_latam_identification_type_id = record.get('l10n_latam_identification_type_id', False)
            
            #Buscar un tipo por defecto si está configurada
            if not l10n_latam_identification_type_id:
               res = self.env['l10n_latam.identification.type'].search([('by_default','=',True)])
               l10n_latam_identification_type_id = res and res[0].id or False
              
            ref = record.get('ref', False)
            dv = record.get('dv', False)
            parent_id = record.get('parent_id', False)
            res_dv = self.check_identification(l10n_latam_identification_type_id, ref, dv)
            record['dv'] = res_dv

            if not parent_id:
               record['ref'] = ref
              
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        l10n_latam_identification_type_id = vals.get('l10n_latam_identification_type_id', False)
        ref = vals.get('ref', False)
        #record['ref'] = vat
        dv = vals.get('dv', False)
        parent_id = vals.get('parent_id', False)

      
        #Los contactos hijos no deben heredar la identificación del padre
        if self.parent_id:
           vals['ref'] = False

        return super(ResPartner, self).write(vals)


    def check_identification(self, l10n_latam_identification_type_id, ref, dv):

            l10n_latam_identification_type = self.env['l10n_latam.identification.type'].browse([l10n_latam_identification_type_id])[0]
            if l10n_latam_identification_type.is_digit:
              if (ref and not ref.isdigit()) or (dv and not dv.isdigit()):
                 raise ValidationError(_('El número de identificación y dígito de verificación deben ser solo dígitos'))

            if l10n_latam_identification_type.is_required and not ref:
               raise ValidationError(_('El tipo de identificación %s requiere que ingrese el número', l10n_latam_identification_type.name))

            dv_calculado = self.generate_dv_co(ref)
            if l10n_latam_identification_type.dv_calculated:
               res_dv = dv_calculado
            else:
               res_dv = dv

            if l10n_latam_identification_type.is_vat:
               if not ref or not res_dv:
                  raise ValidationError(_('El tipo de identificación %s requiere que ingrese el número y dígito de verificación', l10n_latam_identification_type.name))

               if not l10n_latam_identification_type.dv_calculated and dv and dv != res_dv:
                  raise ValidationError(_('El número de identificación ingresado no corresponde con el dígito de verificación'))

            return res_dv


    @api.constrains('dv','ref')
    def check_identification_write(self):

            #with_is_vat = self.filtered(lambda x: x.l10n_latam_identification_type_id.is_vat)
            if self.l10n_latam_identification_type_id.is_digit:
              if (self.ref and not self.ref.isdigit()) or (self.dv and not self.dv.isdigit()):
                 raise ValidationError(_('El número de identificación y dígito de verificación deben ser solo dígitos'))

            if self.l10n_latam_identification_type_id.is_required and not self.ref:
               raise ValidationError(_('El tipo de identificación %s requiere que ingrese el número', self.l10n_latam_identification_type_id.name))

            dv = self.generate_dv_co(self.ref)

            if self.l10n_latam_identification_type_id.dv_calculated:
               self.dv = dv
            #else:
               #self.dv = None

            if self.l10n_latam_identification_type_id.is_vat:
               if not self.ref or not self.dv:
                  raise ValidationError(_('El tipo de identificación %s requiere que ingrese el número y dígito de verificación', self.l10n_latam_identification_type_id.name))

               if dv != self.dv:
                  raise ValidationError(_('El número de identificación ingresado no corresponde con el dígito de verificación'))

            #if not self.parent_id:
            #   self.ref = self.ref



    #def check_digito_verificacion(self):

    #        #with_is_vat = self.filtered(lambda x: x.l10n_latam_identification_type_id.is_vat)
    #        if self.l10n_latam_identification_type_id.is_digit:
    #          if (self.ref and not self.ref.isdigit()) or (self.dv and not self.dv.isdigit()):
    #             raise ValidationError(_('El número de identificación y dígito de verificación deben ser solo dígitos'))

    #        if self.l10n_latam_identification_type_id.is_required and not self.ref:
    #           raise ValidationError(_('El tipo de identificación %s requiere que ingrese el número', self.l10n_latam_identification_type_id.name))

    #        dv = self.generate_dv_co(self.ref)
    #        if self.l10n_latam_identification_type_id.dv_calculated:
    #           self.dv = dv
    #        else:
    #           self.dv = None

    #        if self.l10n_latam_identification_type_id.is_vat:
    #           if not self.ref or not self.dv:
    #              raise ValidationError(_('El tipo de identificación %s requiere que ingrese el número y dígito de verificación', self.l10n_latam_identification_type_id.name))

    #           if dv != self.dv:
    #              raise ValidationError(_('El número de identificación ingresado no corresponde con el dígito de verificación'))
             
    #        if not self.parent_id:
    #           self.ref = self.ref

    @api.model
    def generate_dv_co(self, ref):
        if not ref:
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

        
    #@api.depends('ref', 'company_id')
    #def _compute_same_vat_partner_id(self):
    #    for partner in self:
    #        # use _origin to deal with onchange()
    #        partner_id = partner._origin.id
            
    #        #active_test = False because if a partner has been deactivated you still want to raise the error,
    #        #so that you can reactivate it instead of creating a new one, which would loose its history.
    #        Partner = self.with_context(active_test=False).sudo()
            
    #        domain = [
    #            ('ref', '=', partner.ref),
    #            ('company_id', 'in', [False, partner.company_id.id]),
    #        ]
    #        if partner_id:
    #            domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
    #        partner.same_vat_partner_id = bool(partner.ref) and not partner.parent_id and Partner.search(domain, limit=1)

