import django.contrib.postgres.fields
from django.db import migrations, models

# Fills the new `glide_codes` array field from the old free-text `glide_code`.
# <=18 chars: kept as-is, wrapped in an array (already a valid single code).
# >18 chars: split "A and B" / "A; B" into multiple codes, or extract the id
# from "GDACS ID: <value>" / "GDCS ID: <value>" (misspelling seen in the
# data). Anything else wasn't a real code - left empty.
#
# chr(...) below strips zero-width-space/BOM/nbsp padding; used instead of
# U&'[\200B...]' since some SQL clients choke on that syntax.
FORWARD_SQL = """
UPDATE {table}
SET glide_codes = CASE
    -- Already within the new per-code limit: keep the value as-is, wrapped in
    -- an array. Only strings over 18 chars (multi-code / padded / GDACS refs)
    -- go through parsing.
    WHEN length(glide_code) <= 18 THEN ARRAY[glide_code]::varchar(18)[]
    ELSE COALESCE(
        (
            SELECT array_agg(m[1])
            FROM regexp_matches(glide_code, '[A-Z]{{2}}-[0-9]{{4}}-[0-9]{{6}}-[A-Z]{{3}}', 'g') AS m
        ),
        CASE
            WHEN glide_code ~* 'GD(A)?CS\\s*ID\\s*:\\s*(.+)' THEN
                ARRAY[
                    btrim(
                        regexp_replace(
                            regexp_replace(glide_code, '.*GD(A)?CS\\s*ID\\s*:\\s*', '', 'i'),
                            '[' || chr(8203) || chr(8204) || chr(8205) || chr(65279) || chr(160) || ']', '', 'g'
                        )
                    )
                ]
            ELSE ARRAY[]::varchar[]
        END
    )
END
WHERE glide_code IS NOT NULL AND glide_code != '';
"""

REVERSE_SQL = """
UPDATE {table}
SET glide_code = array_to_string(glide_codes, ' and ')
WHERE glide_codes IS NOT NULL AND glide_codes != '{{}}';
"""

GLIDE_CODES_FIELD = django.contrib.postgres.fields.ArrayField(
    base_field=models.CharField(max_length=18), blank=True, default=list, size=None, verbose_name="glide number"
)


class Migration(migrations.Migration):
    dependencies = [
        ("dref", "0090_drefsummary"),
    ]

    operations = [
        migrations.AddField(model_name="dref", name="glide_codes", field=GLIDE_CODES_FIELD),
        migrations.AddField(model_name="drefoperationalupdate", name="glide_codes", field=GLIDE_CODES_FIELD),
        migrations.AddField(model_name="dreffinalreport", name="glide_codes", field=GLIDE_CODES_FIELD),

        migrations.RunSQL(
            sql=FORWARD_SQL.format(table="dref_dref"),
            reverse_sql=REVERSE_SQL.format(table="dref_dref"),
        ),
        migrations.RunSQL(
            sql=FORWARD_SQL.format(table="dref_drefoperationalupdate"),
            reverse_sql=REVERSE_SQL.format(table="dref_drefoperationalupdate"),
        ),
        migrations.RunSQL(
            sql=FORWARD_SQL.format(table="dref_dreffinalreport"),
            reverse_sql=REVERSE_SQL.format(table="dref_dreffinalreport"),
        ),
        migrations.RemoveField(model_name="dref", name="glide_code"),
        migrations.RemoveField(model_name="drefoperationalupdate", name="glide_code"),
        migrations.RemoveField(model_name="dreffinalreport", name="glide_code"),
    ]
