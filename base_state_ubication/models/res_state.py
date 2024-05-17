# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (c) 2017 Innovatecsa S.A.S. (http://www.innovatecsa.com).
#
##############################################################################

from odoo import api, fields, models, tools, _

class ResState(models.Model):
    _inherit = 'res.country.state'
    _description = 'Ciudades'
    _order = "name"

    #@api.model
    def name_get(self):
        """ Forms complete name of location from parent location to child location. """
        res = []
        for state in self:
            current = state
            name = current.name
            while current.parent_id:
                #name = '%s / %s' % (current.parent_id.name, name)
                name = '%s / %s' % (name, current.parent_id.name)
                current = current.parent_id

            res.append((state.id, name))
        return res
 
    def _compute_complete_name(self):
        """ Forms complete name of location from parent location to child location. """
        for state in self:
            current = state
            name = current.name
            while current.parent_id:
                name = '%s / %s' % (current.parent_id.name, name)
                current = current.parent_id
        return name

    def _search_complete_name(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        states = self.browse()
        if name and operator in ['=', 'ilike']:
            states = self.search([('name', '=', name)] + args, limit=limit)
        if not states:
            states = self.search([('name', operator, name)] + args, limit=limit)
        #return states.name_get()
        return states.name
            
    complete_name = fields.Char(compute='_compute_complete_name', search='_search_complete_name')
    parent_id = fields.Many2one('res.country.state','Departamento', domain=[('type','=','view')])
    child_ids = fields.One2many('res.country.state', 'parent_id', string='Child States')
    type = fields.Selection([('view','View'), ('normal','Normal')], 'Tipo', default='normal')
    active = fields.Boolean('Activo', required=True, default=True)

