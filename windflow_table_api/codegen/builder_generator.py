from typing import Any, List, Optional
from jinja2 import Environment
from windflow_table_api import WindowType


class BuilderGenerator:
    """
    Gestisce il rendering dei template Jinja2 per i Builder e i costrutti di piping C++ di WindFlow.
    L'ambiente dato in input deve essere aperto in codegen/templates/ .
    """

    def __init__(self, jinja_env: Environment) -> None:
        self._jinja_env = jinja_env

    def source_builder(
        self,
        var_name: str,
        out_struct: str,
        filepath: str,
        parser_func: str,
        op_name: str,
        has_header: bool = True,
        event_time: bool = False,
        is_ordered: bool = True,
        delay: Optional[int] = None,
        par: int = 1,
        split_size: int = 0,
    ) -> str:
        template = self._jinja_env.get_template("nodes/source_builder.jinja2")
        return template.render(
            var_name=var_name,
            out_struct=out_struct,
            filepath=filepath,
            parser_func=parser_func,
            op_name=op_name,
            has_header=has_header,
            event_time=event_time,
            is_ordered=is_ordered,
            delay=delay,
            par=par,
            split_size=split_size,
        )

    def where_builder(
        self,
        var_name: str,
        in_struct: str,
        filt_func: str,
        op_name: str,
        par: int = 1,
    ) -> str:
        template = self._jinja_env.get_template("nodes/where_builder.jinja2")
        return template.render(
            var_name=var_name,
            filt_func=filt_func,
            in_struct=in_struct,
            op_name=op_name,
            par=par,
        )

    def select_builder(
        self,
        var_name: str,
        in_struct: str,
        out_struct: str,
        map_func: str,
        op_name: str,
        par: int = 1,
    ) -> str:
        template = self._jinja_env.get_template("nodes/select_builder.jinja2")
        return template.render(
            var_name=var_name,
            in_struct=in_struct,
            out_struct=out_struct,
            map_func=map_func,
            op_name=op_name,
            par=par,
        )

    def group_builder(
        self,
        var_name: str,
        in_struct: str,
        out_struct: str,
        lambda_func: str,
        op_name: str,
        par: int = 1,
        needs_key: bool = False,
        key_struct: Optional[str] = None,
        key_lambda: Optional[str] = None,
        is_windowed: bool = False,
        win_type: Optional[str] = None,
        win_size: Optional[Any] = None,
        win_slide: Optional[Any] = None,
    ) -> str:
        template = self._jinja_env.get_template("nodes/group_builder.jinja2")
        return template.render(
            var_name=var_name,
            in_struct=in_struct,
            out_struct=out_struct,
            lambda_func=lambda_func,
            needs_key=needs_key,
            key_struct=key_struct,
            key_lambda=key_lambda,
            is_windowed=is_windowed,
            win_time= (win_type == WindowType.TIME), 
            win_size=win_size,
            win_slide=win_slide,
            op_name=op_name,
            par=par,
        )

    def distinct_builder(
        self,
        var_name: str,
        in_struct: str,
        op_name: str,
        par: int = 1,
        key_struct: Optional[str] = None,
        key_lambda: Optional[str] = None,
    ) -> str:
        template = self._jinja_env.get_template("nodes/distinct_builder.jinja2")
        return template.render(
            var_name=var_name,
            in_struct=in_struct,
            key_struct=key_struct or in_struct,
            key_lambda=key_lambda,
            op_name=op_name,
            par=par,
        )

    def join_builder(
        self,
        var_name: str,
        in_struct: str,
        out_struct: str,
        join_func: str,
        op_name: str,
        par: int = 1,
        needs_key: bool = False,
        key_struct: Optional[str] = None,
        key_lambda: Optional[str] = None,
        is_windowed: bool = False,
        win_size: Optional[Any] = None,
        win_slide: Optional[Any] = None,
        lower: Optional[int] = None,
        upper: Optional[int] = None,
    ) -> str:
        template = self._jinja_env.get_template("nodes/join_builder.jinja2")
        return template.render(
            var_name=var_name,
            in_struct=in_struct,
            out_struct=out_struct,
            join_func=join_func,
            needs_key=needs_key,
            key_lambda=key_lambda,
            key_struct=key_struct,
            is_windowed=is_windowed,
            win_size=win_size,
            win_slide=win_slide,
            lower=lower,
            upper=upper,
            op_name=op_name,
            par=par,
        )

    def intersect_builder(
        self,
        var_name: str,
        in_struct: str,
        op_name: str,
        is_all: bool = False,
        par: int = 1,
    ) -> str:
        template = self._jinja_env.get_template("nodes/intersect_builder.jinja2")
        return template.render(
            var_name=var_name,
            in_struct=in_struct,
            is_all=is_all,
            op_name=op_name,
            par=par,
        )

    def sink_builder(
        self,
        var_name: str,
        in_struct: str,
        filename: str,
        formatter_func: str,
        op_name: str,
        par: int = 1,
        header_str: Optional[str] = None,
    ) -> str:
        template = self._jinja_env.get_template("nodes/sink_builder.jinja2")
        return template.render(
            var_name=var_name,
            in_struct=in_struct,
            filepath=filename,
            formatter_func=formatter_func,
            header_str=header_str,
            op_name=op_name,
            par=par,
        )

    def merge_pipes(
        self,
        out_pipe: str,
        branches: List[str],
        branches_var: Optional[str] = None,
        topology_name: str = "topology",
    ) -> str:
        template = self._jinja_env.get_template("nodes/merge_pipes.jinja2")
        return template.render(
            out_pipe=out_pipe,
            branches_var=branches_var or f"{out_pipe}_branches",
            branches=branches,
            topology_name=topology_name,
        )
