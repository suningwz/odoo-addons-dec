from openupgradelib import openupgrade

_model_renames = [
    ('licence.licence', 'software.license'),
    ('licence.application', 'software.license.application'),
]

_table_renames = [
    (old.replace('.', '_'), new.replace('.', '_'))
    for (old, new) in _model_renames
]

@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    if openupgrade.table_exists(cr, 'licence_licence'):
        openupgrade.rename_models(cr, _model_renames)
        if openupgrade.table_exists(cr, 'software_license'):
            cr.execute("DROP TABLE software_license;")
        if openupgrade.table_exists(cr, 'software_license_application'):
            cr.execute("DROP TABLE software_license_application;")
        openupgrade.rename_tables(cr, _table_renames)
