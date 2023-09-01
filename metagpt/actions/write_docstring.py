"""Code Docstring Generator.

This script provides a tool to automatically generate docstrings for Python code. It uses the specified style to create
docstrings for the given code and system text.

Usage:
    python3 -m metagpt.actions.write_docstring <filename> [--overwrite] [--style=<docstring_style>]

Arguments:
    filename           The path to the Python file for which you want to generate docstrings.

Options:
    --overwrite        If specified, overwrite the original file with the code containing docstrings.
    --style=<docstring_style>   Specify the style of the generated docstrings.
                                Valid values: 'google', 'numpy', or 'sphinx'.
                                Default: 'google'

Example:
    python3 -m metagpt.actions.write_docstring startup.py --overwrite False --style=numpy

This script uses the 'fire' library to create a command-line interface. It generates docstrings for the given Python code using
the specified docstring style and adds them to the code.
"""
import ast
from typing import Literal

from metagpt.actions.action import Action
from metagpt.utils.common import OutputParser
from metagpt.utils.pycst import merge_docstring

PYTHON_DOCSTRING_SYSTEM = '''### Requirements
1. Add docstrings to the given code following the {style} style.
2. Replace the function body with an Ellipsis object(...) to reduce output.
3. If the types are already annotated, there is no need to include them in the docstring.
4. Extract only class, function or the docstrings for the module parts from the given Python code, avoiding any other text.

### Input Example
```python
def function_with_pep484_type_annotations(param1: int) -> bool:
    return isinstance(param1, int)

class ExampleError(Exception):
    def __init__(self, msg: str):
        self.msg = msg
```

### Output Example
```python
{example}
```
'''

# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html

PYTHON_DOCSTRING_EXAMPLE_GOOGLE = '''
def function_with_pep484_type_annotations(param1: int) -> bool:
    """Example function with PEP 484 type annotations.

    Extended description of function.

    Args:
        param1: The first parameter.

    Returns:
        The return value. True for success, False otherwise.
    """
    ...

class ExampleError(Exception):
    """Exceptions are documented in the same way as classes.

    The __init__ method was documented in the class level docstring.

    Args:
        msg: Human readable string describing the exception.

    Attributes:
        msg: Human readable string describing the exception.
    """
    ...
'''

PYTHON_DOCSTRING_EXAMPLE_NUMPY = '''
def function_with_pep484_type_annotations(param1: int) -> bool:
    """
    Example function with PEP 484 type annotations.

    Extended description of function.

    Parameters
    ----------
    param1
        The first parameter.

    Returns
    -------
    bool
        The return value. True for success, False otherwise.
    """
    ...

class ExampleError(Exception):
    """
    Exceptions are documented in the same way as classes.

    The __init__ method was documented in the class level docstring.

    Parameters
    ----------
    msg
        Human readable string describing the exception.

    Attributes
    ----------
    msg
        Human readable string describing the exception.
    """
    ...
'''

PYTHON_DOCSTRING_EXAMPLE_SPHINX = '''
def function_with_pep484_type_annotations(param1: int) -> bool:
    """Example function with PEP 484 type annotations.

    Extended description of function.

    :param param1: The first parameter.
    :type param1: int

    :return: The return value. True for success, False otherwise.
    :rtype: bool
    """
    ...

class ExampleError(Exception):
    """Exceptions are documented in the same way as classes.

    The __init__ method was documented in the class level docstring.

    :param msg: Human-readable string describing the exception.
    :type msg: str
    """
    ...
'''

_python_docstring_style = {
    "google": PYTHON_DOCSTRING_EXAMPLE_GOOGLE.strip(),
    "numpy": PYTHON_DOCSTRING_EXAMPLE_NUMPY.strip(),
    "sphinx": PYTHON_DOCSTRING_EXAMPLE_SPHINX.strip(),
}


CSHARP_XML_SYSTEM = '''### Requirements
1. Add XML comment to the given code following the {style} style.
2. Replace the function body with an Ellipsis object(...) to reduce output.
3. If the types are already annotated, there is no need to include them in the docstring.
4. Extract only class, function or the XML comments for the module parts from the given C# code, avoiding any other text.

### Input Example
```csharp
class GenericClass<T>
{
    // Fields and members.
}
public class ParamsAndParamRefs
{
    public static T GetGenericValue<T>(T para)
    {
        return para;
    }
}
```

### Output Example
```csharp
{example}
```
'''

CSHARP_XML_EXAMPLE_MS = '''
/// <summary>
/// This is a generic class.
/// </summary>
/// <remarks>
/// This example shows how to specify the <see cref="GenericClass{T}"/>
/// type as a cref attribute.
/// In generic classes and methods, you'll often want to reference the
/// generic type, or the type parameter.
/// </remarks>
class GenericClass<T>
{
    // Fields and members.
}

/// <Summary>
/// This shows examples of typeparamref and typeparam tags
/// </Summary>
public class ParamsAndParamRefs
{
    /// <summary>
    /// The GetGenericValue method.
    /// </summary>
    /// <remarks>
    /// This sample shows how to specify the <see cref="GetGenericValue"/>
    /// method as a cref attribute.
    /// The parameter and return value are both of an arbitrary type,
    /// <typeparamref name="T"/>
    /// </remarks>
    public static T GetGenericValue<T>(T para)
    {
        return para;
    }
}
'''

_csharp_xml_style = {
    "ms": CSHARP_XML_EXAMPLE_MS.strip(),
}

class WriteXMLComment(Action):
    """This class is used to write docstrings for code.

    Attributes:
        desc: A string describing the action.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.desc = "Write docstring for code."

    async def run(
        self, code: str,
        system_text: str = CSHARP_XML_SYSTEM,
        style: Literal["google", "numpy", "sphinx"] = "google",
    ) -> str:
        """Writes XML comment for the given code and system text in the specified style.

        Args:
            code: A string of C# code.
            system_text: A string of system text.
            style: A string specifying the style of the docstring. Can be 'google', 'numpy', or 'sphinx'.

        Returns:
            The C# code with docstrings added.
        """
        system_text = system_text.format(style=style, example=_csharp_xml_style[style])
        #simplified_code = _simplify_python_code(code)
        documented_code = await self._aask(f"```csharp\n{code}\n```", [system_text])
        documented_code = OutputParser.parse_python_code(documented_code)
        return merge_docstring(code, documented_code)


def _simplify_python_code(code: str) -> None:
    """Simplifies the given Python code by removing expressions and the last if statement.

    Args:
        code: A string of Python code.

    Returns:
        The simplified Python code.
    """
    code_tree = ast.parse(code)
    code_tree.body = [i for i in code_tree.body if not isinstance(i, ast.Expr)]
    if isinstance(code_tree.body[-1], ast.If):
        code_tree.body.pop()
    return ast.unparse(code_tree)


if __name__ == "__main__":
    import fire

    async def run(filename: str, overwrite: bool = False, style: Literal["google", "numpy", "sphinx"] = "google"):
        with open(filename) as f:
            code = f.read()
        code = await WriteXMLComment().run(code, style=style)
        if overwrite:
            with open(filename, "w") as f:
                f.write(code)
        return code

    fire.Fire(run)
