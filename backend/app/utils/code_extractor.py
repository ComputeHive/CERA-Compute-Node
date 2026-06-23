import ast
import re
from pathlib import Path
from typing import Dict, Optional

from app.executor.models.flattenedcode import FlattenedCode
from app.executor.utils.logging_config import get_logger

logger = get_logger(__name__)


class CodeExtractor:
    def extract_from_string(self, content: str) -> FlattenedCode:
        requirements = self._extract_requirements(content)
        code_content = self._extract_code_block(content)
        function_name = self._extract_target_name(code_content)
        function_cont, code_deps = self._split_target(
            code_content, function_name
        )
        logger.debug("Target function name: %s", function_name)
        input_schema = self._extract_input_schema(function_cont)
        return FlattenedCode(
            requirements=requirements,
            code_deps=code_deps,
            function_content=function_cont,
            function_name=str(function_name) if function_name else "",
            input_schema=input_schema,
        )

    def extract_from_file(self, file_path: str) -> FlattenedCode:
        content = Path(file_path).read_text(encoding="utf-8")
        logger.info("Extracting code from file: %s", file_path)
        requirements = self._extract_requirements(content)
        code_content = self._extract_code_block(content)
        function_name = self._extract_target_name(code_content)
        function_cont, code_deps = self._split_target(
            code_content, function_name
        )
        logger.debug("Target function name: %s", function_name)
        input_schema = self._extract_input_schema(function_cont)
        return FlattenedCode(
            requirements=requirements,
            code_deps=code_deps,
            function_content=function_cont,
            function_name=str(function_name) if function_name else "",
            input_schema=input_schema,
        )

    def _extract_input_schema(
        self, function_content: str
    ) -> Dict[str, Optional[str]]:
        tree = ast.parse(function_content)
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        )
        return {
            arg.arg: (ast.unparse(arg.annotation) if arg.annotation else None)
            for arg in func.args.args
        }

    def _extract_requirements(self, content: str) -> str:
        match = re.search(
            r"```requirements\.txt\n(.*?)```", content, re.DOTALL
        )
        return match.group(1).strip() if match else ""

    def _extract_code_block(self, content: str) -> str:
        match = re.search(r"```code\n(.*?)```", content, re.DOTALL)
        return match.group(1) if match else ""

    def _extract_target_name(self, code_content: str) -> Optional[str]:
        match = re.search(r"#\s*Target:\s*(\w+)", code_content)
        return match.group(1) if match else None

    def _split_target(
        self, code_content: str, function_name: Optional[str]
    ) -> tuple[str, str]:
        if not function_name:
            return "", code_content.strip()
        pattern = (
            rf"(^def {re.escape(function_name)}\b.*?)(?=^(?:def|class)\s|\Z)"
        )
        match = re.search(pattern, code_content, re.DOTALL | re.MULTILINE)
        if not match:
            return "", code_content.strip()
        function_cont = match.group(1).strip()
        code_deps = code_content.replace(match.group(1), "").strip()
        return function_cont, code_deps
