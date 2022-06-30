from django.db.models import Func
from django.db.models.constraints import Deferrable
from django_pg_ddl_extras import (
    ConstraintTrigger,
    PostgresFunctionDefinition,
    PostgresTriggerFunctionDefinition,
    TriggerEvent,
)


def test_constraint_trigger():
    trigger = (
        ConstraintTrigger(
            name="my_trigger",
            events=[TriggerEvent.UPDATE, TriggerEvent.INSERT, TriggerEvent.DELETE],
            deferrable=Deferrable.DEFERRED,
            function=Func(function="LOWER"),
        ),
    )
    assert trigger


def test_pg_function_definition():
    custom_function = PostgresFunctionDefinition(
        name="my_function",
        returns="trigger",
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

    assert custom_function


def test_pg_trigger_function_definition():
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

    assert custom_function
