import logging
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import Enum

import config
from src.core.ollama_client import OllamaClient, get_ollama_client

logger = logging.getLogger(__name__)


class CodeLanguage(Enum):
    PYTHON = "python"
    SQL = "sql"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    R = "r"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    GENERIC = "generic"


LANGUAGE_PROMPTS = {
    CodeLanguage.PYTHON: """Voce e um especialista em Python.
Regras:
- Use type hints em todas as funcoes
- Siga PEP 8
- Prefira list/dict comprehensions quando apropriado
- Use pathlib para caminhos de arquivo
- Use f-strings para formatacao
- Docstrings apenas se explicitamente pedido""",
    CodeLanguage.SQL: """Voce e um especialista em SQL.
Regras:
- Use CTEs quando apropriado para legibilidade
- Prefira JOINs explicitos sobre implicitos
- Use aliases significativos
- Formate queries para legibilidade
- Considere performance (indices, particoes)""",
    CodeLanguage.JAVASCRIPT: """Voce e um especialista em JavaScript/TypeScript.
Regras:
- Use const/let, nunca var
- Prefira arrow functions
- Use async/await sobre callbacks
- Destructuring quando apropriado
- ES6+ features""",
    CodeLanguage.BASH: """Voce e um especialista em Bash/Shell scripting.
Regras:
- Use set -euo pipefail no inicio
- Quote variaveis sempre
- Use [[ ]] sobre [ ]
- Funcoes para codigo reutilizavel
- Comentarios para comandos complexos""",
    CodeLanguage.GENERIC: """Voce e um assistente de programacao.
Responda com codigo limpo e bem estruturado.
Sem explicacoes longas, apenas codigo e comentarios breves quando necessario.""",
}


@dataclass
class CodeResponse:
    code: str
    language: str
    explanation: str | None = None
    raw_response: str | None = None
    error: str | None = None


class QwenCoder:
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self.model = model or config.CODE_LOCAL.get("model", "qwen2.5-coder:7b")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client: OllamaClient | None = None

    def _get_client(self) -> OllamaClient:
        if self._client is None:
            self._client = get_ollama_client()
        return self._client

    def _detect_language(self, prompt: str) -> CodeLanguage:
        prompt_lower = prompt.lower()

        if any(kw in prompt_lower for kw in ["python", "pandas", "numpy", "pip", "django", "flask", "fastapi"]):
            return CodeLanguage.PYTHON
        if any(
            kw in prompt_lower for kw in ["sql", "query", "select", "insert", "update", "delete", "join", "bigquery"]
        ):
            return CodeLanguage.SQL
        if any(kw in prompt_lower for kw in ["javascript", "js", "node", "react", "vue", "npm"]):
            return CodeLanguage.JAVASCRIPT
        if any(kw in prompt_lower for kw in ["typescript", "ts", "angular"]):
            return CodeLanguage.TYPESCRIPT
        if any(kw in prompt_lower for kw in ["bash", "shell", "script", "terminal", "linux", "chmod"]):
            return CodeLanguage.BASH
        if any(kw in prompt_lower for kw in [" r ", "rstudio", "tidyverse", "ggplot", "dplyr"]):
            return CodeLanguage.R

        return CodeLanguage.PYTHON

    def _extract_code(self, response: str, language: CodeLanguage) -> tuple[str, str | None]:
        code_block_pattern = r"```(?:\w+)?\n(.*?)```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)

        if matches:
            code = "\n\n".join(m.strip() for m in matches)
            explanation = re.sub(code_block_pattern, "", response, flags=re.DOTALL).strip()
            return code, explanation if explanation else None

        lines = response.split("\n")
        code_lines = []
        explanation_lines = []
        in_code = False

        for line in lines:
            stripped = line.strip()
            if (
                stripped.startswith(
                    (
                        "def ",
                        "class ",
                        "import ",
                        "from ",
                        "SELECT",
                        "INSERT",
                        "UPDATE",
                        "CREATE",
                        "function ",
                        "const ",
                        "let ",
                        "var ",
                        "#!/",
                    )
                )
                or stripped.startswith(("#!", "if ", "for ", "while ", "try:", "except"))
                or (in_code and (line.startswith("    ") or line.startswith("\t") or not stripped))
            ):
                in_code = True
                code_lines.append(line)
            else:
                if code_lines and stripped:
                    explanation_lines.append(line)
                elif not code_lines:
                    explanation_lines.append(line)

        code = "\n".join(code_lines).strip()
        explanation = "\n".join(explanation_lines).strip()

        return code if code else response, explanation if explanation else None

    async def generate(
        self,
        prompt: str,
        language: CodeLanguage | None = None,
        context: str | None = None,
    ) -> CodeResponse:
        client = self._get_client()

        if language is None:
            language = self._detect_language(prompt)

        system_prompt = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS[CodeLanguage.GENERIC])

        if context:
            full_prompt = f"Contexto do codigo existente:\n```\n{context}\n```\n\nPedido: {prompt}"
        else:
            full_prompt = prompt

        response = await client.generate(
            prompt=full_prompt,
            model=self.model,
            system=system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        if response.error:
            return CodeResponse(
                code="",
                language=language.value,
                error=response.error,
                raw_response=response.text,
            )

        code, explanation = self._extract_code(response.text, language)

        return CodeResponse(
            code=code,
            language=language.value,
            explanation=explanation,
            raw_response=response.text,
        )

    async def generate_stream(
        self,
        prompt: str,
        language: CodeLanguage | None = None,
    ) -> AsyncGenerator[str, None]:
        client = self._get_client()

        if language is None:
            language = self._detect_language(prompt)

        system_prompt = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS[CodeLanguage.GENERIC])

        async for chunk in client.generate_stream(
            prompt=prompt,
            model=self.model,
            system=system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ):
            yield chunk

    async def fix_code(
        self,
        code: str,
        error_message: str,
        language: CodeLanguage | None = None,
    ) -> CodeResponse:
        prompt = f"""Corrija o seguinte erro no codigo:

Codigo:
```
{code}
```

Erro:
{error_message}

Retorne APENAS o codigo corrigido."""

        return await self.generate(prompt, language)

    async def explain_code(
        self,
        code: str,
        language: CodeLanguage | None = None,
    ) -> str:
        client = self._get_client()

        prompt = f"""Explique o seguinte codigo de forma breve e direta:

```
{code}
```

Explicacao:"""

        response = await client.generate(
            prompt=prompt,
            model=self.model,
            system="Voce explica codigo de forma concisa e tecnica. Sem introducoes, va direto ao ponto.",
            temperature=0.5,
            max_tokens=1024,
        )

        return response.text if not response.error else f"[Erro: {response.error}]"

    async def is_available(self) -> bool:
        client = self._get_client()
        if not await client.check_health():
            return False
        return await client.model_exists(self.model)

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


_instance: QwenCoder | None = None


def get_qwen_coder() -> QwenCoder:
    global _instance
    if _instance is None:
        _instance = QwenCoder()
    return _instance


async def quick_code(prompt: str, language: str = "python") -> str:
    coder = get_qwen_coder()
    lang = CodeLanguage(language) if language in [l.value for l in CodeLanguage] else CodeLanguage.PYTHON
    response = await coder.generate(prompt, lang)
    if response.error:
        return f"[Erro: {response.error}]"
    return response.code
