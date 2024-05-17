# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2024 INNOVATECSA S.A.S (<http://www.innovatecsa.com>).
#
##############################################################################
{
    "name": "Impuestos - Localización Colombiana",
    "version": "17.0",
    "description": """
This module allows to evaluate a tax at invoice level, using parameters such as total base and others. 

Too adds a float field on the fiscal year to fill a value used as parameter such the Colombian UVT or Peruvian UIT.

    """,
    "author": "INNOVATECSA S.A.S",
    "website": "http://www.innovatecsa.com",
    "license": "Other proprietary",
    "category": "Financial",
    "depends": [
		    "account",
			"sale",
			"purchase",
            "account_accountant",
			#"om_account_accountant",
			#"purchase_discount",
			],
	"data":[
		    "views/account_tax_view.xml",
			"views/account_journal_view.xml",
			],
    "demo_xml": [
			],
    "active": False,
    "installable": True,
    "certificate" : "",
	'images': [
            '/static/description/icon.png'
              ],
}

