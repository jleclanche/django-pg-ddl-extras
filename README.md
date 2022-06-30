# django-pg-ddl-extras

A tiny library that implements declarative postgres function definitions for Django.

## Requirements

-   Python >= 3.7
-   Django >= 3.2

## Usage

In the below example, we create a function that is run as part of a constraint trigger.

```py
from django_pg_ddl_extras import (
    PostgresTriggerFunctionDefinition,
    ConstraintTrigger,
    TriggerEvent,
)
from django.db import models
from django.db.models.constraints import Deferrable

# Write a custom constraint in SQL
# In order to get picked up by the migration engine, we include the function definition
# as part of the class `Meta.constraints` list.
# Unfortunately, Django does not seem to have a cleaner way to define this yet.
custom_function = PostgresTriggerFunctionDefinition(
    name="my_function",
    body="""
DECLARE
BEGIN
    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    END IF;
    IF NOT FOUND THEN
        RAISE EXCEPTION
            'This is an example constraint error'
            USING ERRCODE = 23514;
    END IF;
    RETURN NEW;
END;
    """,
)

class MyModel(models.Model):
    class Meta:
        constraints = [
            custom_function,
            ConstraintTrigger(
                name="my_trigger",
                events=[TriggerEvent.UPDATE, TriggerEvent.INSERT, TriggerEvent.DELETE],
                deferrable=Deferrable.DEFERRED,
                function=custom_function.as_func(),
            ),
        ]

```
