"""
..  Copyright © 2022-2024 PsiQuantum Corp.  All rights reserved.
    PSIQUANTUM CORP. CONFIDENTIAL
    This file includes unpublished proprietary source code of PsiQuantum Corp.
    The copyright notice above does not evidence any actual or intended publication
    of such source code. Disclosure of this source code or any related proprietary
    information is strictly prohibited without the express written permission of
    PsiQuantum Corp.

Utilities for rendering estimators in LaTeX.
"""

from typing import Optional

from sympy import latex, symbols

from ._routine import Routine
from .compilation._utilities import split_equation
from .symbolics.sympy_interpreter import parse_to_sympy


# TODO: the functions below should almost work, but they previously accepted an estimator
# They have to be changd so they accept precisely the data they operate on.
# other differences would be in naming of the sections:
# costs -> resources
# inherited params -> linked params
# local parameters -> local variables
# register sizes -> port sizes
# TODO: add return types
def _format_input_params(input_params: list[str]):
    """Formats estimator input parameters to LaTeX."""
    input_params = [_format_param(input_param) for input_param in input_params]
    return _format_section_one_line("Input parameters", input_params)


def _format_linked_params(linked_params):
    """Formats estimator inherited parameters to LaTeX."""
    lines = []
    for param, children_links in linked_params.items():
        key = _format_param_math(param)
        param_names = [".".join([link[0].name, link[1]]) for link in children_links]
        values = [_format_param(param) for param in param_names]
        lines.append(f"&{key}: " + ", ".join(values))
    return _format_section_multi_line("Linked parameters", lines)


def _format_input_port_sizes(ports):
    values = []
    for port in ports.values():
        values.append(rf"{_format_param_text(port.name)}.\!{_format_param_math(port.size)}")
    return _format_section_one_line("Input ports", values)


def _format_output_port_sizes(ports):
    """Returns the output register sizes formatted in LaTeX."""
    lines = []
    for port in ports.values():
        port_name = port.name
        lines.append(f"&{_format_param_text(port_name)} = {_latex_expression(port.size)}")
    return _format_section_multi_line("Output ports", lines)


def _format_local_variables(local_variables):
    """Formats estimator local parameters to LaTeX."""
    lines = []
    for variable in local_variables:
        assignment, expression = split_equation(variable)
        lines.append(f"&{_format_param_math(assignment)} = {_latex_expression(expression)}")
    return _format_section_multi_line("Local variables", lines)


SECTIONS = [
    # pairs of the form (get_line_data, format_line_data)
    # TODO: actually implement the functions listed below, base on the estimator-based ones further in this file
    # TODO: ordering of this list matters, make sure it is correct
    ("input_params", _format_input_params),
    ("linked_params", _format_linked_params),
    ("input_ports", _format_input_port_sizes),
    ("output_ports", _format_output_port_sizes),
    ("local_variables", _format_local_variables),
]


def represent_routine_in_latex(routine: Routine, show_non_root_resources: Optional[bool] = True) -> str:
    """Returns a snippet of LaTeX used to render the routine using clear LaTeX.

    Args:
        routine: The routine to render.
        show_non_root_costs: If ``True`` (default), displays all costs, otherwise only includes costs
        from the root node.

    Returns:
        A LaTeX snippet of the routine.
    """
    lines = [format_line(data) for attr_name, format_line in SECTIONS if (data := getattr(routine, attr_name))]

    # We deal with resources separately due to show_non_root_resources option
    if resource_section := _format_resources(routine, show_non_root_resources):
        lines.append(resource_section)

    return "\\begin{align}\n" + "\\\\\n".join(lines) + "\n\\end{align}"


def _format_section_one_line(header, entries):
    """Formats a parameter section into a bolded header followed by a comma-separated list of entries."""
    return f"&\\bf\\text{{{header}:}}\\\\\n&" + ", ".join(entries)


def _format_section_multi_line(header, lines):
    """Formats a parameter section into a bolded header followed by a series of lines."""
    return f"&\\bf\\text{{{header}:}}\\\\\n" + "\\\\\n".join(lines)


def _format_param(param):
    if "." in param:
        path, local_param = param.rsplit(".", 1)
        return rf"{_format_param_text(path)}.\!{_format_local_param(local_param)}"
    return _format_local_param(param)


def _format_local_param(param):
    """Formats a non-dot-separated parameter based upon what would render best."""
    return _format_param_math(param) if param.count("_") <= 1 else _format_param_text(param)


def _format_param_text(param):
    """Formats a param as text."""
    return rf"\text{{{param}}}"


def _format_param_math(param):
    """Formats a param as math."""
    if "_" in param:
        return _format_param_math_with_subscript(param)
    return latex(symbols(param))


def _format_param_math_with_subscript(param):
    """Formats a subscripted param as math."""
    symbol, subscript = param.split("_", 1)
    subscript_latex = latex(symbols(subscript))
    symbol_latex = latex(symbols(symbol))

    # If subscript contains something that needs LaTeX to render, use that, but render text as text.
    # For example, if subscript is "lambda", this will become "\\lambda", which we want to render symbolically.
    if r"\\" in subscript_latex:
        subscript = subscript_latex
    else:
        subscript = rf"\text{{{subscript}}}"

    return rf"{symbol_latex}_{{{subscript}}}"


def _latex_expression(expression: str) -> str:
    """Maps an expression string to valid LaTeX."""
    sympy_expression = parse_to_sympy(str(expression))
    symbol_names = {symbol: _format_param(str(symbol)) for symbol in sympy_expression.free_symbols}
    return latex(sympy_expression, symbol_names=symbol_names, mul_symbol="dot")


def _format_resources(routine: Routine, show_non_root_resources: bool):
    lines = []
    lines += _get_resources_lines(routine.resources)
    for subroutine in routine.walk():
        if subroutine != routine and show_non_root_resources:
            lines += _get_resources_lines(subroutine.resources, subroutine.name)
    if len(lines) > 0:
        return _format_section_multi_line("Resources", lines)


def _get_resources_lines(resources, path=None):
    """Formats estimator costs to LaTeX."""
    lines = []
    for resource in resources.values():
        if path is None:
            resource_path = resource.name
        else:
            resource_path = f"{path}.{resource.name}"
        lines.append(f"&{_format_param(resource_path)} = {_latex_expression(resource.value)}")
    return lines
