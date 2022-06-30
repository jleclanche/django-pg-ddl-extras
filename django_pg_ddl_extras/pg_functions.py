from django.db.backends.ddl_references import Statement, Table
from django.db.models import Func

_PG_FUNC_DEF_TEMPLATE = """
CREATE FUNCTION %(name)s() RETURNS %(returns)s AS
$$
%(body)s
$$ LANGUAGE %(language)s;
"""


class PostgresFunctionDefinition:
    create_template = _PG_FUNC_DEF_TEMPLATE.replace("\n", " ").strip()
    remove_template = "DROP FUNCTION %(name)s()"

    def __init__(self, name: str, body: str, returns: str, language: str = "plpgsql"):
        self.name = name
        self.body = body.strip()
        self.returns = returns
        self.language = language

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.name == other.name
                and self.body == other.body
                and self.returns == other.returns
                and self.language == other.language
            )
        return super().__eq__(other)

    def create_sql(self, model, schema_editor) -> Statement:
        table = Table(model._meta.db_table, schema_editor.quote_name)
        function_body = Statement(self.body, table=table)

        return Statement(
            self.create_template,
            name=self.name,
            returns=self.returns,
            body=str(function_body),
            language=self.language,
        )

    def remove_sql(self, model, schema_editor) -> Statement:
        return Statement(self.remove_template, name=self.name)

    def clone(self):
        _, args, kwargs = self.deconstruct()
        return self.__class__(*args, **kwargs)

    def deconstruct(self):
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        return (
            path,
            (),
            {
                "name": self.name,
                "body": self.body,
                "returns": self.returns,
                "language": self.language,
            },
        )

    def as_func(self) -> Func:
        return Func(function=self.name)


class PostgresTriggerFunctionDefinition(PostgresFunctionDefinition):
    def __init__(self, *args, **kwargs):
        kwargs["returns"] = "trigger"
        super().__init__(*args, **kwargs)
