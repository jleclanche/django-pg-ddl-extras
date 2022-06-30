from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from django.db.backends.ddl_references import Statement, Table
from django.db.models import Func
from django.db.models.constraints import BaseConstraint, Deferrable
from django.db.models.expressions import BaseExpression
from django.db.models.sql import Query


class TriggerEvent(Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


_TriggerEventLike = Union[Literal["INSERT", "UPDATE", "DELETE"], TriggerEvent]


_CONSTRAINT_TRIGGER_TEMPLATE = """
CREATE CONSTRAINT TRIGGER %(name)s
AFTER %(events)s ON %(table)s%(deferrable)s
FOR EACH ROW %(condition)s
EXECUTE PROCEDURE %(procedure)s
"""


class ConstraintTrigger(BaseConstraint):
    template = _CONSTRAINT_TRIGGER_TEMPLATE.strip()
    delete_template = "DROP TRIGGER %(name)s ON %(table)s"

    def __init__(
        self,
        *,
        name: str,
        events: Union[List[_TriggerEventLike], Tuple[_TriggerEventLike, ...]],
        function: Func,
        condition: Optional[BaseExpression] = None,
        deferrable: Optional[Deferrable] = None,
    ):
        self.function = function
        self.condition = condition
        self.deferrable = deferrable
        self.events = tuple(
            e.value if isinstance(e, TriggerEvent) else str(e).upper() for e in events
        )

        if not self.events:
            raise ValueError(
                "ConstraintTrigger events must be a list of at least one TriggerEvent"
            )

        super().__init__(name)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.name == other.name
                and set(self.events) == set(other.events)
                and self.function == other.function
                and self.condition == other.condition
                and self.deferrable == other.deferrable
            )

        return super().__eq__(other)

    def _get_condition_sql(self, compiler, schema_editor, query) -> str:
        if self.condition is None:
            return ""

        sql, params = self.condition.as_sql(compiler, schema_editor.connection)
        condition_sql = sql % tuple(schema_editor.quote_value(p) for p in params)

        return "WHEN %s" % (condition_sql)

    def _get_procedure_sql(self, compiler, schema_editor) -> str:
        sql, params = self.function.as_sql(compiler, schema_editor.connection)

        return sql % tuple(schema_editor.quote_value(p) for p in params)

    def create_sql(self, model, schema_editor) -> Statement:
        assert model
        assert schema_editor
        table = Table(model._meta.db_table, schema_editor.quote_name)
        query = Query(model, alias_cols=False)
        compiler = query.get_compiler(connection=schema_editor.connection)
        condition = self._get_condition_sql(compiler, schema_editor, query)

        return Statement(
            self.template,
            name=schema_editor.quote_name(self.name),
            events=" OR ".join(self.events),
            table=table,
            condition=condition,
            deferrable=schema_editor._deferrable_constraint_sql(self.deferrable),
            procedure=self._get_procedure_sql(compiler, schema_editor),
        )

    def remove_sql(self, model, schema_editor) -> Statement:
        assert model
        assert schema_editor
        return Statement(
            self.delete_template,
            table=Table(model._meta.db_table, schema_editor.quote_name),
            name=schema_editor.quote_name(self.name),
        )

    def deconstruct(self) -> Tuple[str, Tuple[Any, ...], Dict[str, Any]]:
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        kwargs = {
            "name": self.name,
            "events": self.events,
            "function": self.function,
        }
        if self.condition:
            kwargs["condition"] = self.condition
        if self.deferrable is not None:
            kwargs["deferrable"] = self.deferrable

        return path, (), kwargs
