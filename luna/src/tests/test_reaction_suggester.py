import asyncio

import pytest


class TestReactionAliases:
    def test_aliases_exist(self):
        from src.ui.reaction_suggester import REACTION_ALIASES

        assert len(REACTION_ALIASES) > 0

    def test_contains_common_aliases(self):
        from src.ui.reaction_suggester import REACTION_ALIASES

        assert "/reacao" in REACTION_ALIASES
        assert "/react" in REACTION_ALIASES


class TestReactionSuggesterInit:
    def test_creates_instance(self):
        from src.ui.reaction_suggester import ReactionSuggester

        suggester = ReactionSuggester()

        assert suggester is not None
        assert len(suggester._reactions) > 0

    def test_has_pattern(self):
        from src.ui.reaction_suggester import ReactionSuggester

        suggester = ReactionSuggester()

        assert suggester._pattern is not None


class TestReactionSuggesterGetSuggestion:
    def test_returns_none_for_no_match(self):
        from src.ui.reaction_suggester import ReactionSuggester

        suggester = ReactionSuggester()

        result = asyncio.run(suggester.get_suggestion("hello world"))

        assert result is None

    def test_suggests_for_react_command(self):
        from src.ui.reaction_suggester import ReactionSuggester

        suggester = ReactionSuggester()

        result = asyncio.run(suggester.get_suggestion("/react apai"))

        assert result is not None
        assert "apaixonada" in result.lower()

    def test_suggests_default_for_empty_partial(self):
        from src.ui.reaction_suggester import ReactionSuggester

        suggester = ReactionSuggester()

        result = asyncio.run(suggester.get_suggestion("/react "))

        assert result is not None
        assert "/react" in result.lower()

    def test_suggests_for_reacao_command(self):
        from src.ui.reaction_suggester import ReactionSuggester

        suggester = ReactionSuggester()

        result = asyncio.run(suggester.get_suggestion("/reacao cur"))

        assert result is not None
        assert "curiosa" in result.lower()

    def test_preserves_prefix(self):
        from src.ui.reaction_suggester import ReactionSuggester

        suggester = ReactionSuggester()

        result = asyncio.run(suggester.get_suggestion("some text /react obs"))

        assert result is not None
        assert result.startswith("some text ")


class TestGetAvailableReactions:
    def test_returns_list(self):
        from src.ui.reaction_suggester import get_available_reactions

        result = get_available_reactions()

        assert isinstance(result, list)

    def test_contains_reactions(self):
        from src.ui.reaction_suggester import get_available_reactions

        result = get_available_reactions()

        assert len(result) > 0

    def test_reactions_are_strings(self):
        from src.ui.reaction_suggester import get_available_reactions

        result = get_available_reactions()

        for reaction in result:
            assert isinstance(reaction, str)


class TestGetReactionDescriptions:
    def test_returns_dict(self):
        from src.ui.reaction_suggester import get_reaction_descriptions

        result = get_reaction_descriptions()

        assert isinstance(result, dict)

    def test_contains_descriptions(self):
        from src.ui.reaction_suggester import get_reaction_descriptions

        result = get_reaction_descriptions()

        assert len(result) > 0

    def test_has_common_reactions(self):
        from src.ui.reaction_suggester import get_reaction_descriptions

        result = get_reaction_descriptions()

        assert "Luna_feliz" in result
        assert "Luna_triste" in result
        assert "Luna_observando" in result

    def test_descriptions_are_strings(self):
        from src.ui.reaction_suggester import get_reaction_descriptions

        result = get_reaction_descriptions()

        for key, value in result.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
