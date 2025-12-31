"""
EntityLoader - Carregamento de entidades do panteao.

Gerencia configuracoes e assets das entidades (Luna, Eris, Juno, etc):
- Carrega config.json de cada entidade
- Gerencia fallback para Luna quando entidade indisponivel
- Fornece animacoes, cores e personalidade por entidade
- Mantem perfil de usuario com entidade ativa

Classes principais:
    EntityLoader: Carregador de entidades

Funcoes globais:
    get_active_entity(): Retorna EntityLoader da entidade ativa
    set_active_entity(entity_id): Muda entidade ativa
    get_entity_name(): Nome da entidade ativa

Dependencias:
    - src.core.file_lock: Leitura segura de JSON
"""

from src.core.entity_loader import (
    DEFAULT_BANNER,
    DEFAULT_COLORS,
    DEFAULT_GRADIENT,
    ENTITIES_DIR,
    PANTEAO_DIR,
    PROFILE_PATH,
    REGISTRY_PATH,
    EntityLoader,
    darken_color,
    generate_static_base,
    get_active_entity,
    get_active_loader,
    get_entity_name,
    get_entity_phrases,
    hex_to_rgb,
    lighten_color,
    reload_active_loader,
    rgb_to_hex,
    set_active_entity,
)

__all__ = [
    "EntityLoader",
    "get_active_entity",
    "set_active_entity",
    "get_entity_phrases",
    "get_entity_name",
    "get_active_loader",
    "reload_active_loader",
    "PANTEAO_DIR",
    "REGISTRY_PATH",
    "ENTITIES_DIR",
    "PROFILE_PATH",
    "DEFAULT_COLORS",
    "DEFAULT_GRADIENT",
    "DEFAULT_BANNER",
    "hex_to_rgb",
    "rgb_to_hex",
    "lighten_color",
    "darken_color",
    "generate_static_base",
]
