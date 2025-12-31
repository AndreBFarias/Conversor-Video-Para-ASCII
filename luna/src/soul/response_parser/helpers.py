from src.core.entity_loader import get_active_entity, get_entity_name


def get_entity_prefix() -> str:
    return get_entity_name(get_active_entity())


def get_simple_prompt_format() -> str:
    entity_name = get_entity_prefix()
    return f"""RESPONDA NESTE FORMATO EXATO (separado por ponto e virgula):
fala: sua resposta aqui; tom: emocao; animacao: {entity_name}_X; visao: false

Exemplo:
fala: E ai mortal, o que quer dessa vez?; tom: tedio; animacao: {entity_name}_sarcastica; visao: false

ANIMACOES VALIDAS: {entity_name}_observando, {entity_name}_sarcastica, {entity_name}_curiosa, {entity_name}_feliz, {entity_name}_irritada, {entity_name}_triste, {entity_name}_apaixonada, {entity_name}_flertando, {entity_name}_neutra, {entity_name}_piscando, {entity_name}_sensualizando, {entity_name}_obssecada

Responda APENAS neste formato, sem explicacoes extras."""


_parser_instance = None


def get_parser():
    from .parser import UniversalResponseParser

    global _parser_instance
    if _parser_instance is None:
        _parser_instance = UniversalResponseParser()
    return _parser_instance
