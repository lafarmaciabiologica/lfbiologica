# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Doxoo S.A.S (<http://www.doxoo.co>).
#
##############################################################################
{
    "name": "Natural Person",
    "version": "17.0",
    "description": """
Add Natural Person to Partner Object and RUT/NIT to ref.
    """,
    "author": "DOXOO S.A.S",
    "website": "http://www.doxoo.co",
    "category": "Tools",
    "depends": [
            'base',
            'l10n_co',
			],
	"data":[
		    "views/res_partner_view.xml",
            "views/l10n_latam_identification_type_view.xml",
            "data/l10n_latam.identification.type.csv",
            #"data/type_identification_data.xml",
            "security/ir.model.access.csv",
			],
    "demo_xml": [
			],
    "update_xml": [
			],
    "active": False,
    "installable": True,
    "certificate" : "",
    'license': "Other proprietary",
}

