{
    'name': "DHTMLX Gantt",

    'summary': """
        Interactive HTML5 DHTMLX-based Gantt View 
        """,

    'description': """
        
    """,
    "category": "Project Management",

    'author': "Ubay Abdelgadir, Paul Automation",
    'website': "https://paulautomation.com",
    'license': "GPL-3",
    
    # 'website': "https://github.com/obayit/odoo_dhtmlxgantt",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project Management',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'project',        
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/dhx_assets.xml',
        'views/dhx_task.xml',
        'views/dhx_project.xml',
    ],
    'qweb': [
        "static/src/xml/dhx_gantt.xml",
    ],
    'images': [
        'images/screenshot_1.png'
    ],
    'application': True,
    'installable': True,        
    'uninstall_hook': 'dhx_uninstall_hook'

}