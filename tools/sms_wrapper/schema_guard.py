#!/usr/bin/env python3
"""schema_guard.py — instancia de schema JSON validada ANTES de selar.

BIBLIOTECA (isenta do sweep do validate_measurement_tools, como png_io):
quem a usa para nao selar instancia invalida e o measure_runtime_probe.py.

Ressalva da L035 (curadoria 2026-09-04): o produtor escrevia
"schema": "runtime_metrics_v1" como string literal e nunca abria o arquivo
do schema — a ponta escrita sem a travessia, a forma do defeito que o
pacote veio curar. Este modulo e a travessia.

DESIGN fail-closed: o validador suporta SOMENTE o subconjunto de keywords
que os schemas deste wrapper usam (ver SUPPORTED). Keyword conhecida da
linguagem JSON Schema mas nao suportada aqui (pattern, oneOf,
additionalProperties, ...) REPROVA a validacao com erro explicito em vez
de ser ignorada em silencio — validador que pula keyword que nao entende
aprova instancia que nao devia. $schema/title/description sao metadados e
sao ignorados de propósito.
"""
import json
import os

SUPPORTED = {"type", "required", "properties", "enum",
             "maximum", "minimum", "items"}
METADATA = {"$schema", "title", "description"}


class SchemaUnsupported(Exception):
    """O schema usa keyword que este validador nao implementa."""


def load_schema(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def schema_path(wrapper_dir=None):
    """Caminho do runtime_metrics_v1.schema.json ao lado das ferramentas."""
    if wrapper_dir is None:
        wrapper_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(wrapper_dir, "schemas", "runtime_metrics_v1.schema.json")


def _type_ok(instance, expected):
    checks = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float))
                            and not isinstance(v, bool),
        "null": lambda v: v is None,
    }
    if expected not in checks:
        raise SchemaUnsupported(f"tipo '{expected}' fora do subconjunto")
    return checks[expected](instance)


def validate(instance, schema, path="$"):
    """Lista de violacoes; vazia = instancia conforme. PURA.

    Enum/maximum/minimum so se aplicam a instancias nao-nulas: o schema
    permite null via type list, e null nao viola maximum.
    """
    if not isinstance(schema, dict):
        return [f"{path}: schema nao e um objeto"]
    viol = []
    for kw in schema:
        if kw in SUPPORTED or kw in METADATA:
            continue
        raise SchemaUnsupported(
            f"{path}: keyword '{kw}' nao suportada por este validador "
            "(fail-closed: estenda o validador ou reveja o schema)")

    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        if not any(_type_ok(instance, t) for t in types):
            viol.append(f"{path}: tipo {type(instance).__name__} fora de "
                        f"{types}")
            return viol          # sem tipo base, as outras checagens mentem

    if "enum" in schema and instance is not None:
        if instance not in schema["enum"]:
            viol.append(f"{path}: {instance!r} fora do enum "
                        f"{schema['enum']}")

    for kw in ("maximum", "minimum"):
        if kw in schema and isinstance(instance, (int, float)) \
                and not isinstance(instance, bool):
            lim = schema[kw]
            if (kw == "maximum" and instance > lim) or \
               (kw == "minimum" and instance < lim):
                viol.append(f"{path}: {instance} viola {kw}={lim}")

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                viol.append(f"{path}: campo obrigatorio ausente: '{req}'")
        for name, sub in schema.get("properties", {}).items():
            if name in instance:
                viol += validate(instance[name], sub, f"{path}.{name}")

    if isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            viol += validate(item, schema["items"], f"{path}[{i}]")
    return viol
