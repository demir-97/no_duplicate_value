from odoo import api, fields, models, _
# Odoo 20 moved ormcache to odoo.api; importing it from odoo.tools still
# works but raises a DeprecationWarning.
from odoo.api import ormcache
from odoo.exceptions import ValidationError

SUPPORTED_TTYPES = ['char', 'text', 'selection', 'integer', 'float']


class DuplicateValueRule(models.Model):
    _name = 'no_duplicate_value.rule'
    _description = 'No Duplicate Value Rule'
    _order = 'model_name, field_name'
    # Odoo 20 dropped registry.clear_cache() in favour of declaring which
    # ormcache a model invalidates: the ORM then clears it on every create,
    # write and unlink of this model by itself (_clear_cache_on_fields left
    # at None means "any field"). That replaces the create/write/unlink
    # overrides this module carried on 17-19, and also covers the flush
    # paths those overrides missed.
    _clear_cache_name = 'default'

    name = fields.Char(compute='_compute_name', store=True)
    model_id = fields.Many2one(
        'ir.model', string='Model', required=True, ondelete='cascade',
        domain=[('transient', '=', False)],
    )
    model_name = fields.Char(string='Model (technical name)', related='model_id.model', store=True, readonly=True)
    field_id = fields.Many2one(
        'ir.model.fields', string='Field', required=True, ondelete='cascade',
        domain="[('model_id', '=', model_id), ('ttype', 'in', %s), ('store', '=', True)]" % (SUPPORTED_TTYPES,),
    )
    field_name = fields.Char(related='field_id.name', store=True, readonly=True)
    case_insensitive = fields.Boolean(
        string='Case-insensitive', default=True,
        help='"ABC-001" and "abc-001" are treated as the same value.',
    )
    company_scoped = fields.Boolean(
        string='Scope to company',
        help="If the model has a Company field, only compare records of the same company.",
    )
    error_message = fields.Char(
        string='Custom error message',
        help='Leave empty to use the default message. Use %(value)s and %(field)s to include the '
             'offending value and field name.',
    )
    active = fields.Boolean(default=True)

    @api.depends('model_id.name', 'field_id.field_description')
    def _compute_name(self):
        for rule in self:
            if rule.model_id and rule.field_id:
                rule.name = _("%(model)s: %(field)s", model=rule.model_id.name, field=rule.field_id.field_description)
            else:
                rule.name = _("New Rule")

    @api.constrains('model_id', 'field_id')
    def _check_field_belongs_to_model(self):
        for rule in self:
            if rule.field_id and rule.model_id and rule.field_id.model_id != rule.model_id:
                raise ValidationError(_("The selected field must belong to the selected model."))

    @api.model
    @ormcache('model_name')
    def _get_active_rules(self, model_name):
        """Cached: active rules for a given model, as plain dicts (cheap to
        read, no recordset kept alive across the cache)."""
        rules = self.sudo().search([('model_name', '=', model_name), ('active', '=', True)])
        return [
            {
                'field_name': rule.field_name,
                'field_description': rule.field_id.field_description,
                'case_insensitive': rule.case_insensitive,
                'company_scoped': rule.company_scoped,
                'error_message': rule.error_message,
            }
            for rule in rules
        ]
