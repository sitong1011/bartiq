"""
..  Copyright © 2022-2023 PsiQuantum Corp.  All rights reserved.
    PSIQUANTUM CORP. CONFIDENTIAL
    This file includes unpublished proprietary source code of PsiQuantum Corp.
    The copyright notice above does not evidence any actual or intended publication
    of such source code. Disclosure of this source code or any related proprietary
    information is strictly prohibited without the express written permission of
    PsiQuantum Corp.

Tests for Estimators' LaTeX rendering.
"""

import pytest

from bartiq import Routine
from bartiq.latex import represent_routine_in_latex


# TODO: convert expected outputs having in mind that now we have:
# - resources instead of costs
# - ports/port sizes instead of registers/register sizes
# - linked_params instead of inherited params
# - local variables instead of local parameters
@pytest.mark.parametrize(
    "routine, kwargs, expected_latex",
    [
        # Null case
        (
            Routine(name="root"),
            {},
            "\n\n",
        ),
        # Only input parameters
        (
            Routine(name="root", input_params=["x", "y"]),
            {},
            r"""
&\bf\text{Input parameters:}\\
&x, y
""",
        ),
        # Path-prefixed input parameters
        (
            Routine(
                name="root",
                input_params=["subroutine.x_a", "y_b"],
                children={"subroutine": {"name": "subroutine", "input_params": ["x_a"]}},
            ),
            {},
            r"""
&\bf\text{Input parameters:}\\
&\text{subroutine}.\!x_{\text{a}}, y_{\text{b}}
""",
        ),
        # Only inherited_params
        (
            Routine(
                name="root",
                linked_params={
                    "x": [("a", "i_0"), ("c", "j_1")],
                    "y": [("d", "k_2"), ("e", "l_3")],
                },
                children={
                    "a": {"name": "a", "input_params": ["i_0"]},
                    "c": {"name": "c", "input_params": ["j_1"]},
                    "d": {"name": "d", "input_params": ["k_2"]},
                    "e": {"name": "e", "input_params": ["l_3"]},
                },
            ),
            {},
            r"""
&\bf\text{Linked parameters:}\\
&x: \text{a}.\!i_{\text{0}}, \text{c}.\!j_{\text{1}}\\
&y: \text{d}.\!k_{\text{2}}, \text{e}.\!l_{\text{3}}
""",
        ),
        # Only input register sizes
        (
            Routine(
                name="root",
                ports={
                    "0": {"name": "0", "size": "a", "direction": "input"},
                    "b": {"name": "b", "size": "b", "direction": "input"},
                },
            ),
            {},
            r"""
&\bf\text{Input ports:}\\
&\text{0}.\!a, \text{b}.\!b
""",
        ),
        # Only local parameters
        (
            Routine(
                name="root",
                input_params=["a", "b"],
                local_variables=[
                    "x_foo = y + a",
                    "y_bar = b * c",
                ],
            ),
            {},
            r"""
&\bf\text{Input parameters:}\\
&a, b\\
&\bf\text{Local variables:}\\
&x_{\text{foo}} = a + y\\
&y_{\text{bar}} = b \cdot c
""",
        ),
        # Only output ports
        (
            Routine(
                name="root",
                ports={
                    "0": {"name": "0", "size": "2", "direction": "output"},
                    "b": {"name": "b", "size": "3", "direction": "output"},
                },
            ),
            {},
            r"""
&\bf\text{Output ports:}\\
&\text{0} = 2\\
&\text{b} = 3
""",
        ),
        # Only costs
        (
            Routine(
                name="root",
                resources={
                    "x": {"name": "x", "value": 0, "type": "additive"},
                    "y": {"name": "y", "value": 1, "type": "additive"},
                },
            ),
            {},
            r"""
&\bf\text{Resources:}\\
&x = 0\\
&y = 1
""",
        ),
        # The whole shebang
        (
            Routine(
                name="root",
                input_params=["x", "y"],
                ports={
                    "in_0": {"name": "in_0", "size": "a", "direction": "input"},
                    "in_b": {"name": "in_b", "size": "b", "direction": "input"},
                    "out_0": {"name": "out_0", "size": "2", "direction": "output"},
                    "out_b": {"name": "out_b", "size": "3", "direction": "output"},
                },
                linked_params={
                    "x": [("a", "i_0"), ("c", "j_1")],
                    "y": [("d", "k_2"), ("e", "l_3")],
                },
                children={
                    "a": {"name": "a", "input_params": ["i_0"]},
                    "c": {"name": "c", "input_params": ["j_1"]},
                    "d": {"name": "d", "input_params": ["k_2"]},
                    "e": {"name": "e", "input_params": ["l_3"]},
                },
                local_variables=[
                    "x_foo = a.i_0 + a",
                    "y_bar = b * c.j_1",
                ],
                resources={
                    "t": {"name": "t", "value": 0, "type": "additive"},
                },
            ),
            {},
            r"""
&\bf\text{Input parameters:}\\
&x, y\\
&\bf\text{Linked parameters:}\\
&x: \text{a}.\!i_{\text{0}}, \text{c}.\!j_{\text{1}}\\
&y: \text{d}.\!k_{\text{2}}, \text{e}.\!l_{\text{3}}\\
&\bf\text{Input ports:}\\
&\text{in_0}.\!a, \text{in_b}.\!b\\
&\bf\text{Output ports:}\\
&\text{out_0} = 2\\
&\text{out_b} = 3\\
&\bf\text{Local variables:}\\
&x_{\text{foo}} = a + \text{a}.\!i_{\text{0}}\\
&y_{\text{bar}} = b \cdot \text{c}.\!j_{\text{1}}\\
&\bf\text{Resources:}\\
&t = 0
""",
        ),
        # Different whitespace around operands in assignment string
        (
            Routine(
                name="root",
                local_variables=[
                    "a=1+2",
                    "b = 3+4",
                ],
                resources={
                    "c": {"name": "c", "value": "a + b", "type": "additive"},
                    "d": {"name": "d", "value": "a-b", "type": "additive"},
                },
            ),
            {},
            r"""
&\bf\text{Local variables:}\\
&a = 3\\
&b = 7\\
&\bf\text{Resources:}\\
&c = a + b\\
&d = a - b
""",
        ),
        # Don't hide non-root costs (default)
        # Add children, make sure you include them in implementation
        (
            Routine(
                name="root",
                children={
                    "a": {
                        "name": "a",
                        "resources": {
                            "y": {"name": "y", "value": "2", "type": "additive"},
                        },
                    },
                },
                resources={
                    "x": {"name": "x", "value": "1", "type": "additive"},
                },
            ),
            {},
            r"""
&\bf\text{Resources:}\\
&x = 1\\
&\text{a}.\!y = 2
""",
        ),
        # Hide non-root costs
        (
            Routine(
                name="root",
                children={
                    "a": {
                        "name": "a",
                        "resources": {
                            "y": {"name": "y", "value": "2", "type": "additive"},
                        },
                    },
                },
                resources={
                    "x": {"name": "x", "value": "1", "type": "additive"},
                },
            ),
            {"show_non_root_resources": False},
            r"""
&\bf\text{Resources:}\\
&x = 1
""",
        ),
        # Sum over all subcosts
        (
            Routine(
                name="root",
                resources={
                    "N_x": {"name": "N_x", "value": "sum(~.N_x)", "type": "additive"},
                },
            ),
            {},
            r"""
&\bf\text{Resources:}\\
&N_{\text{x}} = \operatorname{sum}{\left(\text{~}.\!N_{\text{x}} \right)}
""",
        ),
    ],
)
def test_represent_routine_in_latex(routine, kwargs, expected_latex):
    expected_string = rf"\begin{{align}}{expected_latex}\end{{align}}"
    assert represent_routine_in_latex(routine, **kwargs) == expected_string