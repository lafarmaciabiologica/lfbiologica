# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
# Copyright (c) 2017 Innovatecsa S.A.S. (http://www.innovatecsa.com).
#
##############################################################################

from odoo import api, fields, models, tools, _

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    @api.onchange('first_name', 'middle_name', 'surname', 'mother_name')
    def onchange_person_name(self):
        self.name = (self.first_name and (self.first_name+' ') or '') + (self.middle_name and (self.middle_name+' ') or '') + (self.surname and (self.surname+' ') or '') + (self.mother_name and (self.mother_name+' ') or '')

