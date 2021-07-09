# -*- coding: utf-8 -*-
# Copyright 2021 Apulia Software s.r.l. (<info@apuliasoftware.it>)
# License AGPL-3 or later (https://www.gnu.org/licenses/agpl-3.0).

{
    'name': "Fatturapa Out Merge Invoice Lines",
    'summary': """
        This module export in xml file all line flagged like details with 
        import zero and create a line with sum of all details line in invoice""",
    'author': "Apulia Software srlu",
    'website': "http://www.apuliasoftware.it",
    'category': 'Account',
    'version': '12.0.1.0.0',
    'depends': [
        'l10n_it_fatturapa_out'
        ],
    'data': [
        'views/account_views.xml',
    ],
}