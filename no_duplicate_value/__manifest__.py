{
    'name': 'No Duplicate Value | Unique Field Rules Without Code',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'author': 'Meisanqo',
    'support': 'meisanqo@outlook.com',
    'summary': 'Block duplicate field values from Settings — no code, no developer.',
    'description': """
No Duplicate Value
====================

Odoo's SQL unique constraints require a developer. This module lets an
administrator configure, from Settings, "this field on this model must be
unique" rules for any stored field on any model — reference numbers, VAT
numbers, SKUs, tag names, whatever needs to stay unique — and get a clear,
friendly error instead of a raw database error, or worse, a silently
duplicated record.

Getting started
----------------

Settings > Technical > No Duplicate Value: create a rule, pick a model and
one of its fields, save. From then on, creating or editing a record with a
value that already exists on another record of that model is blocked with
a clear message.

Options per rule
------------------

- Case-insensitive matching (default on): "ABC-001" and "abc-001" are
  treated as the same value.
- Scope to company: if the model has a `company_id` field, only records of
  the same company are compared.
- Custom error message.
- Enable/disable a rule at any time without deleting it.

Supported field types: Char, Text, Selection, Integer, Float (stored
fields only).

Safety
-------

- Zero rules configured = zero behavior change. The check only runs for
  models and fields you explicitly configure.
- The check runs after the normal save, inside the same database
  transaction: if a duplicate is found, the whole save is rolled back, so
  no bad data is ever left behind.
""",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/duplicate_value_rule_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OPL-1',
    'price': 10.0,
    'currency': 'USD',
}
