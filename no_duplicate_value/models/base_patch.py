"""Adds a post-write duplicate-value check to every model's create/write,
driven entirely by `no_duplicate_value.rule` records (Settings > Technical
> No Duplicate Value). With zero rules configured this adds one cheap
cached dict lookup per create/write and nothing else.

Patching `BaseModel.create`/`write` directly (rather than, say, dynamic
`@api.constrains`) is deliberate: Odoo's inheritance graph is fixed at
registry-build time from each model's own `_inherit`, so there is no
supported way to attach a constraint to a model chosen later, at runtime,
by an administrator through the UI. This is the same technique used by
other "generic rule" modules for the same reason.
"""
import logging

from odoo import api, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

_ORIGINAL_CREATE = models.BaseModel.create
_ORIGINAL_WRITE = models.BaseModel.write


def _normalize(value, case_insensitive):
    if isinstance(value, str) and case_insensitive:
        return value.strip().lower()
    return value


def _run_duplicate_checks(records):
    if not records:
        return
    model_name = records._name
    if model_name == 'no_duplicate_value.rule':
        return
    if 'no_duplicate_value.rule' not in records.env.registry:
        # Mid registry-rebuild (any module install/uninstall/update can hit
        # this), core models may be written to before this module's own
        # model is (re)loaded — skip rather than crash the whole operation.
        return
    rules = records.env['no_duplicate_value.rule']._get_active_rules(model_name)
    if not rules:
        return
    for rule in rules:
        fname = rule['field_name']
        if fname not in records._fields:
            continue
        has_company = rule['company_scoped'] and 'company_id' in records._fields
        for record in records:
            value = record[fname]
            if value is False or value == '':
                continue
            domain = [('id', '!=', record.id)]
            if isinstance(value, str) and rule['case_insensitive']:
                domain.append((fname, '=ilike', value.strip()))
            else:
                domain.append((fname, '=', value))
            if has_company and record.company_id:
                domain.append(('company_id', '=', record.company_id.id))
            duplicate = record.sudo().with_context(active_test=False).search(domain, limit=1)
            if duplicate:
                message = rule['error_message'] or _(
                    'The value "%(value)s" for field "%(field)s" already exists '
                    '(record #%(other_id)s) — duplicate values are not allowed.',
                    value=value, field=rule['field_description'], other_id=duplicate.id,
                )
                raise ValidationError(message)


@api.model_create_multi
def _patched_create(self, vals_list):
    # Must keep the @api.model_create_multi decoration: it's what makes
    # Odoo's RPC dispatch (and any caller passing a single dict instead of
    # a list) marshal arguments the same way the original create() did.
    # Without it, calls coming through /web/dataset/call_kw silently drop
    # the vals argument (TypeError: missing 'vals_list').
    records = _ORIGINAL_CREATE(self, vals_list)
    _run_duplicate_checks(records)
    return records


def _patched_write(self, vals):
    result = _ORIGINAL_WRITE(self, vals)
    _run_duplicate_checks(self)
    return result


if not getattr(models.BaseModel, '_no_duplicate_value_patched', False):
    models.BaseModel.create = _patched_create
    models.BaseModel.write = _patched_write
    models.BaseModel._no_duplicate_value_patched = True
    _logger.info("no_duplicate_value: BaseModel.create/write patched")
