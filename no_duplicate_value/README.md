# No Duplicate Value

**Unique-field rules from Settings — no developer, no SQL.**

Pick a model and a field from **Settings > Technical > No Duplicate Value**
and save: from then on, saving a record with a value that already exists on
another record of that model is blocked with a clear error message, instead
of silently creating a duplicate (or failing with a raw database error).

## Options per rule

- **Case-insensitive** (default on): "ABC-001" and "abc-001" count as the
  same value.
- **Scope to company**: if the model has a Company field, only records of
  the same company are compared.
- **Custom error message**.
- Rules can be disabled without deleting them.

Supported field types: Char, Text, Selection, Integer, Float (stored fields
only).

## Safety

- Zero rules configured = zero behavior change.
- The check runs after the normal save, inside the same database
  transaction, so a blocked save leaves no partial data behind.

## Technical

One configuration model (`no_duplicate_value.rule`) plus a small,
deliberately-scoped extension of `BaseModel.create`/`write` that consults a
cached lookup of active rules — negligible overhead for every model that
has no rule configured. See the code comments in `models/base_patch.py` for
why this needed a base-model extension rather than a per-model constraint.

---
Author: Meisanqo — meisanqo@outlook.com
