# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
# Copyright (c) 2017 Innovatecsa S.A.S. (http://www.innovatecsa.com).
#
##############################################################################

from odoo import api, fields, models, tools, _

class L10nLatamIdentificationType(models.Model):
    _inherit = 'l10n_latam.identification.type'
    _description = "Identification Types"
    _order = 'sequence'

    is_required = fields.Boolean('Requerido', required=True, default=True)
    dv_calculated = fields.Boolean('Calcula DV', required=True, default=False)
    is_digit = fields.Boolean('Es dígito', required=True, default=True)
    by_default = fields.Boolean('Defecto', required=True, default=False)

