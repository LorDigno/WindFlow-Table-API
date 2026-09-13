from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, Annotated
from dataclasses import dataclass, field as dc_field
from pydantic import BaseModel, Field, ConfigDict, model_validator, TypeAdapter

from ..object_names import WindowType, WindowKind, OpType
from ..times import TimeUnits
from .schema_gen import SchemaGenerator, CppStruct
from .expr_translator import ExpressionTranslator
from .lambda_gen import LambdaGenerator
from .builder_generator import BuilderGenerator
from .utility import get_aggregate_default

# =========================================================================
# 1. Contesti di Visita Runtime (immutati, rimangono dataclass)
# =========================================================================

@dataclass
class VisitContext:
    pipe: str
    parent_structs: List[CppStruct]
    to_merge_pipes: List[str]
    sch_gen: SchemaGenerator
    expr_tl: ExpressionTranslator
    lambda_gen: LambdaGenerator
    build_gen: BuilderGenerator
    operations_counter: int
    par: int

@dataclass
class VisitResult:
    out_struct: CppStruct
    pipe_additions: Dict[str, str] = dc_field(default_factory=dict)
    emitted_builders: List[str] = dc_field(default_factory=list)

# =========================================================================
# 2. Sotto-modelli di Validazione (Durate, Finestre, File Config)
# =========================================================================

class DurationModel(BaseModel):
    value: int
    unit: str

    def to_microseconds(self) -> int:
        return TimeUnits.to_microseconds(self.value, self.unit)

class WindowModel(BaseModel):
    type: WindowType
    kind: WindowKind
    size: Union[int, DurationModel]
    slide: Union[int, DurationModel]

    @property
    def size_micros(self) -> int:
        return self.size.to_microseconds() if isinstance(self.size, DurationModel) else self.size

    @property
    def slide_micros(self) -> int:
        return self.slide.to_microseconds() if isinstance(self.slide, DurationModel) else self.slide

class IntervalModel(BaseModel):
    lower_bound: DurationModel
    upper_bound: DurationModel

    @property
    def lower_micros(self) -> int:
        return self.lower_bound.to_microseconds()

    @property
    def upper_micros(self) -> int:
        return self.upper_bound.to_microseconds()

class TimeColModel(BaseModel):
    name: str
    format: str

class SourceConfigModel(BaseModel):
    filepath: str
    header: bool
    file_format: str
    split_size: int
    order: bool
    delay: Optional[DurationModel] = None
    time_col: Optional[TimeColModel] = None

# =========================================================================
# 3. Classi Base AST (BaseModel)
# =========================================================================

class OpNode(BaseModel, ABC):
    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True, arbitrary_types_allowed=True)

    node_id: str
    schema_out: Dict[str, str]
    parents: List[OpNode] = Field(default_factory=list, exclude=True)
    raw_dict: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    @abstractmethod
    def visit(self, ctx: VisitContext) -> VisitResult:
        pass

    def get_map_builder(
        self,
        in_struct: str,
        out_struct: str,
        mappings: List[Tuple[str, str]],
        var_name: str,
        ctx: VisitContext,
    ) -> str:
        map_func = ctx.lambda_gen.map_lambda(
            in_struct=in_struct,
            out_struct=out_struct,
            mappings=mappings,
            input_var="in",
        )
        return ctx.build_gen.select_builder(
            var_name=var_name,
            in_struct=in_struct,
            out_struct=out_struct,
            map_func=map_func,
            op_name=var_name,
            par=ctx.par,
        )

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, OpNode) and self.node_id == other.node_id

class UnaryNode(OpNode, ABC):
    schema_in: Dict[str, str]

class BinaryNode(OpNode, ABC):
    left_schema: Dict[str, str] = Field(alias="tab1_schema")
    right_schema: Dict[str, str] = Field(alias="tab2_schema")

# =========================================================================
# 4. Nodi Sorgente e Sink
# =========================================================================

class FromOpNode(OpNode):
    op_type: Literal[OpType.FROM] = OpType.FROM
    source_table_id: str = Field(alias="source_id")
    config: SourceConfigModel

    def visit(self, ctx: VisitContext) -> VisitResult:
        struct_out = ctx.sch_gen.get_or_create_struct(
            schema_dict=self.schema_out,
            name_hint="source_" + self.node_id,
        )
        time_col_name = self.config.time_col.name if self.config.time_col else None
        time_format = self.config.time_col.format if self.config.time_col else None
        delay_micros = self.config.delay.to_microseconds() if self.config.delay else None

        parser_func = ctx.lambda_gen.parser_lambda(
            struct_out=struct_out.struct_name,
            time_col_name=time_col_name,
            time_format=time_format,
            ordered_fields=[{"name": k, "type": v} for k, v in self.schema_out.items()],
        )

        ctx.operations_counter += 1
        var_name = f"from_{ctx.operations_counter}_op"

        builder_str = ctx.build_gen.source_builder(
            var_name=var_name,
            out_struct=struct_out.struct_name,
            filepath=self.config.filepath,
            parser_func=parser_func,
            op_name=self.node_id,
            has_header=self.config.header,
            event_time=time_col_name is not None,
            is_ordered=self.config.order,
            delay=delay_micros,
            par=ctx.par,
            split_size=self.config.split_size,
        )
        return VisitResult(
            out_struct=struct_out,
            pipe_additions={ctx.pipe: f"auto& {ctx.pipe} = topology.add_source({var_name})"},
            emitted_builders=[builder_str],
        )

class SinkOpNode(OpNode):
    op_type: Literal[OpType.SINK] = OpType.SINK
    filename: str

    def visit(self, ctx: VisitContext) -> VisitResult:
        parent_struct = ctx.parent_structs[0]
        header_str = ",".join(f.name for f in parent_struct.fields)
        formatter_func = ctx.lambda_gen.sink_lambda(
            parent_struct.struct_name,
            fields=parent_struct.fields,
        )
        ctx.operations_counter += 1
        var_name = f"sink_{ctx.operations_counter}_op"

        builder_str = ctx.build_gen.sink_builder(
            var_name=var_name,
            filename=self.filename,
            in_struct=parent_struct.struct_name,
            formatter_func=formatter_func,
            op_name=self.node_id,
            par=ctx.par,
            header_str=header_str,
        )
        return VisitResult(
            out_struct=parent_struct,
            pipe_additions={ctx.pipe: f".add_sink({var_name})"},
            emitted_builders=[builder_str],
        )

# =========================================================================
# 5. Operazioni Unarie
# =========================================================================

class WhereOpNode(UnaryNode):
    op_type: Literal[OpType.WHERE] = OpType.WHERE
    condition: Dict[str, Any]

    def visit(self, ctx: VisitContext) -> VisitResult:
        parent_struct = ctx.parent_structs[0]
        translated_cond = ctx.expr_tl.translate_expr(self.condition)
        filt_func = ctx.lambda_gen.where_lambda(
            in_struct=parent_struct.struct_name,
            condition=translated_cond,
        )
        ctx.operations_counter += 1
        var_name = f"where_{ctx.operations_counter}_op"

        builder_str = ctx.build_gen.where_builder(
            var_name=var_name,
            in_struct=parent_struct.struct_name,
            filt_func=filt_func,
            op_name=self.node_id,
            par=ctx.par,
        )
        return VisitResult(
            out_struct=parent_struct,
            pipe_additions={ctx.pipe: f".add({var_name})"},
            emitted_builders=[builder_str],
        )

class SelectOpNode(UnaryNode):
    op_type: Literal[OpType.SELECT] = OpType.SELECT
    expressions: List[Dict[str, Any]]

    def visit(self, ctx: VisitContext) -> VisitResult:
        parent_struct = ctx.parent_structs[0]
        struct_out = ctx.sch_gen.get_or_create_struct(
            schema_dict=self.schema_out,
            name_hint=self.node_id + "_struct_out",
        )
        mappings = []
        for e in self.expressions:
            val = ctx.expr_tl.translate_expr(e)
            target = e.get("alias") or e.get("name")
            if not target:
                raise KeyError(f"Chiave 'alias' o 'name' assente nell'espressione {e}")
            mappings.append((target, val))

        ctx.operations_counter += 1
        var_name = f"select_{ctx.operations_counter}_op"

        builder_str = self.get_map_builder(
            in_struct=parent_struct.struct_name,
            out_struct=struct_out.struct_name,
            mappings=mappings,
            var_name=var_name,
            ctx=ctx,
        )
        return VisitResult(
            out_struct=struct_out,
            pipe_additions={ctx.pipe: f".add({var_name})"},
            emitted_builders=[builder_str],
        )

class DistinctOpNode(UnaryNode):
    op_type: Literal[OpType.DISTINCT] = OpType.DISTINCT

    def visit(self, ctx: VisitContext) -> VisitResult:
        parent_struct = ctx.parent_structs[0]
        parent_struct.needs_hash = True
        key_lambda = (
            f"[](const {parent_struct.struct_name}& in) -> {parent_struct.struct_name} {{ return in; }}"
            if ctx.par > 1 else None
        )
        ctx.operations_counter += 1
        var_name = f"distinct_{ctx.operations_counter}_op"

        builder_str = ctx.build_gen.distinct_builder(
            var_name=var_name,
            in_struct=parent_struct.struct_name,
            key_struct=parent_struct.struct_name,
            key_lambda=key_lambda,
            op_name=self.node_id,
            par=ctx.par,
        )
        return VisitResult(
            out_struct=parent_struct,
            pipe_additions={ctx.pipe: f".add({var_name})"},
            emitted_builders=[builder_str],
        )

# =========================================================================
# 6. Raggruppamenti (Global & Window)
# =========================================================================

class GroupByNode(UnaryNode, ABC):
    keys: List[str] = Field(default_factory=list)
    aggregations: List[Dict[str, Any]] = Field(default_factory=list)

    def _prepare_group_context(self, ctx: VisitContext, is_windowed: bool):
        parent_struct = ctx.parent_structs[0]
        accs = [ctx.expr_tl.translate_aggregate(a) for a in self.aggregations]
        defaults = {a["name"]: get_aggregate_default(a["func"], a["data_type"]) for a in self.aggregations}

        needs_keyBy = len(self.keys) > 0 and (ctx.par > 1)
        keyBy_struct = None
        keyBy_lambda = None
        if needs_keyBy:
            key_schema = {k: self.schema_in[k] for k in self.keys}
            keyBy_struct = ctx.sch_gen.get_or_create_struct(
                schema_dict=key_schema,
                name_hint=self.node_id + "_key_struct",
                needs_hash=True,
            )
            keyBy_lambda = ctx.lambda_gen.map_lambda(
                in_struct=parent_struct.struct_name,
                out_struct=keyBy_struct.struct_name,
                mappings=[(k, f"in.{k}") for k in key_schema],
                input_var="in",
            )

        struct_out = ctx.sch_gen.get_or_create_struct(
            schema_dict=self.schema_out,
            name_hint=f"{self.node_id}_struct_out",
            needs_win=is_windowed,
            win_key_struct=keyBy_struct,
            defaults=defaults,
        )
        lambda_func = ctx.lambda_gen.groupBy_lambda(
            in_struct=parent_struct.struct_name,
            out_struct=struct_out.struct_name,
            keys=self.keys,
            accumulations=accs,
            in_var="in",
            out_var="out",
        )
        return parent_struct, struct_out, lambda_func, keyBy_struct, keyBy_lambda, needs_keyBy

class GlobalGroupOpNode(GroupByNode):
    op_type: Literal[OpType.GLOBAL_GROUP_BY] = OpType.GLOBAL_GROUP_BY

    def visit(self, ctx: VisitContext) -> VisitResult:
        (parent_struct, struct_out, lambda_func, keyBy_struct, keyBy_lambda, needs_keyBy) = (
            self._prepare_group_context(ctx, is_windowed=False)
        )
        ctx.operations_counter += 1
        var_name = f"global_group_{ctx.operations_counter}_op"

        builder_str = ctx.build_gen.group_builder(
            var_name=var_name,
            in_struct=parent_struct.struct_name,
            out_struct=struct_out.struct_name,
            lambda_func=lambda_func,
            op_name=self.node_id,
            par=ctx.par if needs_keyBy else 1,
            needs_key=needs_keyBy,
            key_struct=keyBy_struct.struct_name if keyBy_struct else None,
            key_lambda=keyBy_lambda,
            is_windowed=False,
        )
        return VisitResult(
            out_struct=struct_out,
            pipe_additions={ctx.pipe: f".add({var_name})"},
            emitted_builders=[builder_str],
        )

class WindowGroupOpNode(GroupByNode):
    op_type: Literal[OpType.WINDOW_GROUP_BY] = OpType.WINDOW_GROUP_BY
    window: WindowModel

    def visit(self, ctx: VisitContext) -> VisitResult:
        (parent_struct, struct_out, lambda_func, keyBy_struct, keyBy_lambda, needs_keyBy) = (
            self._prepare_group_context(ctx, is_windowed=True)
        )
        ctx.operations_counter += 1
        var_name = f"window_group_{ctx.operations_counter}_op"

        builder_str = ctx.build_gen.group_builder(
            var_name=var_name,
            in_struct=parent_struct.struct_name,
            out_struct=struct_out.struct_name,
            lambda_func=lambda_func,
            op_name=self.node_id,
            par=ctx.par if needs_keyBy else 1,
            needs_key=needs_keyBy,
            key_struct=keyBy_struct.struct_name if keyBy_struct else None,
            key_lambda=keyBy_lambda,
            is_windowed=True,
            win_type=self.window.type.value if hasattr(self.window.type, "value") else str(self.window.type),
            win_size=self.window.size_micros,
            win_slide=self.window.slide_micros,
        )
        return VisitResult(
            out_struct=struct_out,
            pipe_additions={ctx.pipe: f".add({var_name})"},
            emitted_builders=[builder_str],
        )

# =========================================================================
# 7. Congiunzioni (Window Join & Interval Join)
# =========================================================================

class JoinNode(BinaryNode, ABC):
    keys: List[str]

    def _prepare_join_context(self, ctx: VisitContext):
        if len(ctx.parent_structs) != 2 or len(ctx.to_merge_pipes) != 2:
            raise RuntimeError(f"Join '{self.node_id}' richiede esattamente 2 struct e 2 pipe in ingresso.")

        left_parent_struct, right_parent_struct = ctx.parent_structs[0], ctx.parent_structs[1]
        left_parent_pipe, right_parent_pipe = ctx.to_merge_pipes[0], ctx.to_merge_pipes[1]

        joined_struct = ctx.sch_gen.struct_join(left_parent_struct, right_parent_struct)
        struct_out = ctx.sch_gen.get_or_create_struct(
            schema_dict=self.schema_out,
            name_hint=self.node_id + "_struct_out",
        )
        result = VisitResult(out_struct=struct_out)

        # Unifier Left
        ctx.operations_counter += 1
        left_map_var = f"left_unifier_{ctx.operations_counter}_op"
        left_map_builder = self.get_map_builder(
            in_struct=left_parent_struct.struct_name,
            out_struct=joined_struct.struct_name,
            mappings=[(f.name, f"in.{f.name}") for f in left_parent_struct.fields],
            var_name=left_map_var,
            ctx=ctx,
        )
        result.emitted_builders.append(left_map_builder)
        result.pipe_additions[left_parent_pipe] = f".add({left_map_var})"

        # Unifier Right
        ctx.operations_counter += 1
        right_map_var = f"right_unifier_{ctx.operations_counter}_op"
        right_map_builder = self.get_map_builder(
            in_struct=right_parent_struct.struct_name,
            out_struct=joined_struct.struct_name,
            mappings=[(f.name, f"in.{f.name}") for f in right_parent_struct.fields],
            var_name=right_map_var,
            ctx=ctx,
        )
        result.emitted_builders.append(right_map_builder)
        result.pipe_additions[right_parent_pipe] = f".add({right_map_var})"

        # KeyBy
        needs_keyBy = ctx.par > 1 and len(self.keys) > 0
        key_lambda, key_struct = None, None
        if needs_keyBy:
            key_schema = {k: self.schema_out[k] for k in self.keys}
            key_struct = ctx.sch_gen.get_or_create_struct(
                schema_dict=key_schema,
                name_hint=self.node_id + "_key_struct",
                needs_hash=True,
            )
            key_lambda = ctx.lambda_gen.map_lambda(
                in_struct=joined_struct.struct_name,
                out_struct=key_struct.struct_name,
                mappings=[(k, f"in.{k}") for k in self.keys],
                input_var="in",
            )

        left_names = {f.name for f in left_parent_struct.fields}
        join_mappings = [
            (f.name, f"left.{f.name}" if f.name in left_names else f"right.{f.name}")
            for f in struct_out.fields
        ]
        join_lambda = ctx.lambda_gen.join_lambda(
            input_struct=joined_struct.struct_name,
            out_struct=struct_out.struct_name,
            mappings=join_mappings,
            left_var="left",
            right_var="right",
        )
        return result, joined_struct, join_lambda, needs_keyBy, key_lambda, key_struct

class WindowJoinOpNode(JoinNode):
    op_type: Literal[OpType.JOIN_WINDOW] = OpType.JOIN_WINDOW
    window: WindowModel = Field(alias="attachment")

    def visit(self, ctx: VisitContext) -> VisitResult:
        result, joined_struct, join_lambda, needs_keyBy, key_lambda, key_struct = (
            self._prepare_join_context(ctx)
        )
        ctx.operations_counter += 1
        var_name = f"join_{ctx.operations_counter}_op"

        builder_str = ctx.build_gen.join_builder(
            var_name=var_name,
            in_struct=joined_struct.struct_name,
            out_struct=result.out_struct.struct_name,
            join_func=join_lambda,
            needs_key=needs_keyBy,
            key_lambda=key_lambda,
            key_struct=key_struct.struct_name if key_struct else None,
            is_windowed=True,
            win_size=self.window.size_micros,
            win_slide=self.window.slide_micros,
            op_name=self.node_id,
            par=ctx.par,
        )
        result.emitted_builders.append(builder_str)
        pipe_str = ctx.build_gen.merge_pipes(
            out_pipe=ctx.pipe,
            branches=ctx.to_merge_pipes,
            branches_var=f"{ctx.pipe}_branches",
        )
        result.pipe_additions[ctx.pipe] = pipe_str + f".add({var_name})"
        return result

class IntervalJoinOpNode(JoinNode):
    op_type: Literal[OpType.JOIN_INTERVAL] = OpType.JOIN_INTERVAL
    interval: IntervalModel = Field(alias="attachment")

    def visit(self, ctx: VisitContext) -> VisitResult:
        result, joined_struct, join_lambda, needs_keyBy, key_lambda, key_struct = (
            self._prepare_join_context(ctx)
        )
        ctx.operations_counter += 1
        var_name = f"join_{ctx.operations_counter}_op"

        builder_str = ctx.build_gen.join_builder(
            var_name=var_name,
            in_struct=joined_struct.struct_name,
            out_struct=result.out_struct.struct_name,
            join_func=join_lambda,
            needs_key=needs_keyBy,
            key_lambda=key_lambda,
            key_struct=key_struct.struct_name if key_struct else None,
            is_windowed=False,
            lower=self.interval.lower_micros,
            upper=self.interval.upper_micros,
            op_name=self.node_id,
            par=ctx.par,
        )
        result.emitted_builders.append(builder_str)
        pipe_str = ctx.build_gen.merge_pipes(
            out_pipe=ctx.pipe,
            branches=ctx.to_merge_pipes,
            branches_var=f"{ctx.pipe}_branches",
        )
        result.pipe_additions[ctx.pipe] = pipe_str + f".add({var_name})"
        return result

# =========================================================================
# 8. Operazioni Insiemistiche (Union & Intersect)
# =========================================================================

class UnionOpNode(BinaryNode):
    op_type: Literal[OpType.UNION, OpType.UNION_ALL]
    is_all: bool = False

    @model_validator(mode="before")
    @classmethod
    def set_flags(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_type = data.get("op_type")
            is_all = raw_type in (OpType.UNION_ALL, "UNION_ALL")
            data["is_all"] = is_all
            data["op_type"] = OpType.UNION_ALL if is_all else OpType.UNION
        return data

    def visit(self, ctx: VisitContext) -> VisitResult:
        left, right = ctx.parent_structs[0], ctx.parent_structs[1]
        if left != right:
            raise RuntimeError(f"Schemi diversi per {self.op_type}: {left.struct_name} vs {right.struct_name}")

        pipe_str = ctx.build_gen.merge_pipes(
            out_pipe=ctx.pipe,
            branches_var=f"{ctx.pipe}_branches",
            branches=ctx.to_merge_pipes,
            topology_name="topology",
        )
        builders = []
        if not self.is_all:
            distinct_node = DistinctOpNode(
                node_id=self.node_id + "_distinct",
                schema_out=self.schema_out,
                schema_in=self.left_schema,
            )
            dist_res = distinct_node.visit(ctx)
            builders = dist_res.emitted_builders
            pipe_str += dist_res.pipe_additions[ctx.pipe]

        return VisitResult(
            out_struct=left,
            emitted_builders=builders,
            pipe_additions={ctx.pipe: pipe_str},
        )

class IntersectOpNode(BinaryNode):
    op_type: Literal[OpType.INTERSECT, OpType.INTERSECT_ALL]
    is_all: bool = False

    @model_validator(mode="before")
    @classmethod
    def set_flags(cls, data: Any) -> Any:
        if isinstance(data, dict):
            raw_type = data.get("op_type")
            is_all = raw_type in (OpType.INTERSECT_ALL, "INTERSECT_ALL")
            data["is_all"] = is_all
            data["op_type"] = OpType.INTERSECT_ALL if is_all else OpType.INTERSECT
        return data

    def visit(self, ctx: VisitContext) -> VisitResult:
        left, right = ctx.parent_structs[0], ctx.parent_structs[1]
        if left != right:
            raise RuntimeError(f"Schemi diversi per {self.op_type}: {left.struct_name} vs {right.struct_name}")

        left.needs_hash = True
        tagged_struct = f"Tagged_Tuple<{left.struct_name}>"
        result = VisitResult(out_struct=left)
        left_pipe, right_pipe = ctx.to_merge_pipes[0], ctx.to_merge_pipes[1]

        # Left tagger
        ctx.operations_counter += 1
        left_var = f"left_tagger_{ctx.operations_counter}_op"
        left_tagger = self.get_map_builder(
            in_struct=left.struct_name,
            out_struct=tagged_struct,
            mappings=[("data", "in"), ("tag", "0")],
            var_name=left_var,
            ctx=ctx,
        )
        result.pipe_additions[left_pipe] = f".chain({left_var})"
        result.emitted_builders.append(left_tagger)

        # Right tagger
        ctx.operations_counter += 1
        right_var = f"right_tagger_{ctx.operations_counter}_op"
        right_tagger = self.get_map_builder(
            in_struct=right.struct_name,
            out_struct=tagged_struct,
            mappings=[("data", "in"), ("tag", "1")],
            var_name=right_var,
            ctx=ctx,
        )
        result.pipe_additions[right_pipe] = f".chain({right_var})"
        result.emitted_builders.append(right_tagger)

        ctx.operations_counter += 1
        var_name = f"intersect_{ctx.operations_counter}_op"
        builder_str = ctx.build_gen.intersect_builder(
            var_name=var_name,
            in_struct=left.struct_name,
            is_all=self.is_all,
            op_name=self.node_id,
            par=ctx.par,
        )
        result.emitted_builders.append(builder_str)

        pipe_str = ctx.build_gen.merge_pipes(
            out_pipe=ctx.pipe,
            branches=ctx.to_merge_pipes,
            branches_var=f"{ctx.pipe}_branches",
        ) + f".add({var_name})"
        result.pipe_additions[ctx.pipe] = pipe_str
        return result

# =========================================================================
# 9. Factory Polimorfica ad Alta Velocità
# =========================================================================

AnyConcreteOpNode = Annotated[
    Union[
        FromOpNode,
        SinkOpNode,
        WhereOpNode,
        SelectOpNode,
        DistinctOpNode,
        GlobalGroupOpNode,
        WindowGroupOpNode,
        WindowJoinOpNode,
        IntervalJoinOpNode,
        UnionOpNode,
        IntersectOpNode,
    ],
    Field(discriminator="op_type"),
]

_node_adapter = TypeAdapter(AnyConcreteOpNode)

class OpNodeFactory:
  """Factory basata sull'Unione Discriminata di Pydantic."""

  @classmethod
  def create(cls, node_id: str, op_dict: Dict[str, Any]) -> OpNode:
    # Rimuoviamo 'parents' per evitare che Pydantic tenti di validare ricorsivamente
    # i sotto-dizionari privi di 'node_id'. La costruzione del grafo (DAG)
    # è già gestita ricorsivamente da parser.py.
    clean_dict = {k: v for k, v in op_dict.items() if k != "parents"}

    payload = {**clean_dict, "node_id": node_id, "raw_dict": op_dict}
    return _node_adapter.validate_python(payload)