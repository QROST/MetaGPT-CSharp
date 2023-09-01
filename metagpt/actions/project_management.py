#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:12
@Author  : alexanderwu
@File    : project_management.py
"""
from typing import List, Tuple

from metagpt.actions.action import Action
from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.common import CodeParser

PROMPT_TEMPLATE = '''
# Context
{context}

## Format example
{format_example}
-----
Role: You are a project manager; the goal is to break down tasks according to PRD/technical design, give a task list, and analyze task dependencies to start with the prerequisite modules
Requirements: Based on the context, fill in the following missing information, note that all sections are returned in C# code triple quote form separately. Here the granularity of the task is a file; if there are any missing files, you can supplement them.
Attention: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the code and triple quote.

## Required C# NuGet Packages: Provided in .csproj XML format

## Required Other Language Packages: Provided in a text format suitable for that language's package manager

## Full API Spec: Use OpenAPI 3.0. Describe all APIs that may be used by both frontend and backend.

## Logic Analysis: Provided as a Python list[str, str]. the first is filename, the second is class/method/function should be implemented in this file. Analyze the dependencies between the files, which work should be done first

## Task list: Provided as Python list[str]. Each str is a filename, the more at the beginning, the more it is a prerequisite dependency, should be done first

## Shared Knowledge: Anything that should be public like static methods, configuration variables details that should be made clear first.

## Anything UNCLEAR: Provide as Plain text. Make clear here. For example, don't forget a main entry. don't forget to init 3rd party libs.

'''

FORMAT_EXAMPLE = '''
---
## Required C# NuGet Packages
```python
"""
<PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
"""
```

## Required Other language third-party packages
```python
"""
No third-party ...
"""
```

## Full API spec
```python
"""
openapi: 3.0.0
...
description: A JSON object ...
"""
```

## Logic Analysis
```python
[
    ("Game.cs", "Contains ..."),
]
```

## Task list
```python
[
    "Game.cs",
]
```

## Shared Knowledge
```python
"""
'Game.cs' contains ...
"""
```

## Anything UNCLEAR
We need ... how to start.
---
'''

OUTPUT_MAPPING = {
    "Required C# NuGet Packages": (str, ...),
    "Required Other language third-party packages": (str, ...),
    "Full API spec": (str, ...),
    "Logic Analysis": (List[Tuple[str, str]], ...),
    "Task list": (List[str], ...),
    "Shared Knowledge": (str, ...),
    "Anything UNCLEAR": (str, ...),
}


class WriteTasks(Action):

    def __init__(self, name="CreateTasks", context=None, llm=None):
        super().__init__(name, context, llm)

    def _generate_csproj_content(self, nuget_packages: str):
        # Generate .csproj content based on NuGet packages
        nuget_xml = ''
        for line in nuget_packages.strip().split('\n'):
            nuget_xml += f'    {line}\n'
        
        csproj_content = f'''<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net5.0</TargetFramework>
  </PropertyGroup>

  <ItemGroup>
{nuget_xml}
  </ItemGroup>

</Project>
'''
        return csproj_content
    
    def _save(self, context, rsp):
        ws_name = CodeParser.parse_str(block="C# Namespace name", text=context[-1].content)
        workspace_path = WORKSPACE_ROOT / ws_name

        # Save API spec and tasks to Markdown
        file_path = workspace_path / 'docs/api_spec_and_tasks.md'
        file_path.write_text(rsp.content)

        # Generate and save .csproj file
        nuget_packages = rsp.instruct_content.dict().get("Required C# NuGet packages").strip('"\n')
        csproj_content = self._generate_csproj_content(nuget_packages)
        csproj_path = workspace_path / f'{ws_name}.csproj'
        csproj_path.write_text(csproj_content)

    async def run(self, context):
        prompt = PROMPT_TEMPLATE.format(context=context, format_example=FORMAT_EXAMPLE)
        rsp = await self._aask_v1(prompt, "task", OUTPUT_MAPPING)
        self._save(context, rsp)
        return rsp


class AssignTasks(Action):
    async def run(self, *args, **kwargs):
        # Here you should implement the actual action
        pass
