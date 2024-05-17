# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
# Copyright (c) 2017 Innovatecsa S.A.S. (http://www.innovatecsa.com).
#
##############################################################################

from odoo import api, fields, models, tools, _


class ResPartner(models.Model):
    
    _name = 'res.partner'
    _inherit = 'res.partner'

    state_id = fields.Many2one("res.country.state", 'Ubication', domain="[('country_id','=',country_id),('type','=','normal')]")

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id:
           self.city = self.state_id.name
        else:
           self.city = False	