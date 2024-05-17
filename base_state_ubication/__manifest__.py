# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Innovatecsa S.A.S (<http://www.innovatecsa.com>).
#
##############################################################################
{
    "name": "States Inherited (Recursive Ubication)",
    "version": "17.0",
    "description": """
        Add parent state to standard state and transform the states on recursive ubication
        """,
    "author": "INNOVATECSA S.A.S",
    "website": "http://www.innovatecsa.com",
    "license": "Other proprietary",
    "category": "Others",
    "depends": ["base"],
    "data":["views/res_state_view.xml",
            "views/res_partner_view.xml",
            ],
    "demo_xml": [ ],
    "update_xml": [ ],
    "active": False,
    "installable": True,
    "certificate" : "",
}

