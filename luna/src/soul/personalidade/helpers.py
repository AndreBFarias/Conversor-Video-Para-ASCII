from .dicionario import DicionarioPersonalidade

_instancia: DicionarioPersonalidade = None


def get_personalidade() -> DicionarioPersonalidade:
    global _instancia
    if _instancia is None:
        _instancia = DicionarioPersonalidade()
    return _instancia
