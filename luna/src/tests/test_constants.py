import pytest


class TestMemoryConstants:
    def test_similarity_thresholds_valid_range(self):
        from src.core.constants import MemoryConstants

        assert 0.0 <= MemoryConstants.SIMILARITY_THRESHOLD <= 1.0
        assert 0.0 <= MemoryConstants.DEDUP_THRESHOLD <= 1.0
        assert 0.0 <= MemoryConstants.MIN_SIMILARITY <= 1.0
        assert MemoryConstants.DEDUP_THRESHOLD > MemoryConstants.SIMILARITY_THRESHOLD

    def test_decay_thresholds_ordered(self):
        from src.core.constants import MemoryConstants

        assert MemoryConstants.DECAY_MIN < MemoryConstants.DECAY_LOW
        assert MemoryConstants.DECAY_LOW < MemoryConstants.DECAY_MEDIUM
        assert MemoryConstants.DECAY_MEDIUM < MemoryConstants.DECAY_HIGH

    def test_adaptive_thresholds_ordered(self):
        from src.core.constants import MemoryConstants

        assert MemoryConstants.ADAPTIVE_THRESHOLD_SHORT < MemoryConstants.ADAPTIVE_THRESHOLD_LONG

    def test_max_context_positive(self):
        from src.core.constants import MemoryConstants

        assert MemoryConstants.MAX_CONTEXT_CHARS > 0
        assert MemoryConstants.MAX_CONTEXT_TOKENS > 0

    def test_min_text_length_reasonable(self):
        from src.core.constants import MemoryConstants

        assert 10 <= MemoryConstants.MIN_TEXT_LENGTH <= 100


class TestCacheConstants:
    def test_ttl_values_positive(self):
        from src.core.constants import CacheConstants

        assert CacheConstants.L1_TTL_SECONDS > 0
        assert CacheConstants.L2_TTL_SECONDS > 0
        assert CacheConstants.L2_TTL_SECONDS > CacheConstants.L1_TTL_SECONDS

    def test_max_size_reasonable(self):
        from src.core.constants import CacheConstants

        assert 100 <= CacheConstants.MAX_SIZE <= 1000
        assert 100 <= CacheConstants.ENTITY_CACHE_MAX_SIZE <= 1000

    def test_similarity_threshold_valid(self):
        from src.core.constants import CacheConstants

        assert 0.5 <= CacheConstants.SIMILARITY_THRESHOLD <= 1.0


class TestAudioConstants:
    def test_sample_rates_standard(self):
        from src.core.constants import AudioConstants

        assert AudioConstants.SAMPLE_RATE in [16000, 22050, 44100, 48000]
        assert AudioConstants.NATIVE_SAMPLE_RATE in [16000, 22050, 44100, 48000]

    def test_channels_mono_or_stereo(self):
        from src.core.constants import AudioConstants

        assert AudioConstants.CHANNELS in [1, 2]

    def test_timeouts_reasonable(self):
        from src.core.constants import AudioConstants

        assert 10 <= AudioConstants.TTS_TIMEOUT <= 120
        assert 5 <= AudioConstants.DAEMON_TIMEOUT <= 60


class TestTTSConstants:
    def test_default_values_in_range(self):
        from src.core.constants import TTSConstants

        assert 0.5 <= TTSConstants.DEFAULT_SPEED <= 2.0
        assert 0.0 <= TTSConstants.DEFAULT_STABILITY <= 1.0
        assert 0.0 <= TTSConstants.DEFAULT_STYLE <= 1.0
        assert 0.0 <= TTSConstants.DEFAULT_EXAGGERATION <= 1.0

    def test_onboarding_values_in_range(self):
        from src.core.constants import TTSConstants

        assert 0.5 <= TTSConstants.ONBOARDING_SPEED <= 2.0
        assert 0.0 <= TTSConstants.ONBOARDING_STABILITY <= 1.0
        assert 0.0 <= TTSConstants.ONBOARDING_STYLE <= 1.0


class TestCircuitBreakerConstants:
    def test_max_failures_positive(self):
        from src.core.constants import CircuitBreakerConstants

        assert CircuitBreakerConstants.MAX_FAILURES >= 1

    def test_reset_timeout_reasonable(self):
        from src.core.constants import CircuitBreakerConstants

        assert 10 <= CircuitBreakerConstants.RESET_TIMEOUT <= 300

    def test_half_open_successes_positive(self):
        from src.core.constants import CircuitBreakerConstants

        assert CircuitBreakerConstants.HALF_OPEN_SUCCESSES >= 1


class TestPersonalityConstants:
    def test_reinforcement_interval_positive(self):
        from src.core.constants import PersonalityConstants

        assert PersonalityConstants.REINFORCEMENT_INTERVAL >= 1

    def test_decay_rate_valid(self):
        from src.core.constants import PersonalityConstants

        assert 0.0 < PersonalityConstants.EMOTION_DECAY_RATE <= 1.0

    def test_proactive_chance_small(self):
        from src.core.constants import PersonalityConstants

        assert 0.0 < PersonalityConstants.PROACTIVE_BASE_CHANCE <= 0.1


class TestEmbeddingConstants:
    def test_dimension_power_of_two_or_common(self):
        from src.core.constants import EmbeddingConstants

        common_dims = [64, 128, 256, 384, 512, 768, 1024]
        assert EmbeddingConstants.DIMENSION in common_dims


class TestSessionConstants:
    def test_summary_interval_positive(self):
        from src.core.constants import SessionConstants

        assert SessionConstants.SUMMARY_INTERVAL >= 1

    def test_consolidation_interval_reasonable(self):
        from src.core.constants import SessionConstants

        assert 5 <= SessionConstants.CONSOLIDATION_INTERVAL_MINUTES <= 120


class TestVisionConstants:
    def test_thresholds_valid(self):
        from src.core.constants import VisionConstants

        assert VisionConstants.CHANGE_THRESHOLD > 0
        assert 0.0 <= VisionConstants.HISTOGRAM_THRESHOLD <= 1.0

    def test_cache_values_reasonable(self):
        from src.core.constants import VisionConstants

        assert VisionConstants.CACHE_TTL > 0
        assert VisionConstants.MAX_CACHE_SIZE > 0


class TestEmotionalConstants:
    def test_confidence_thresholds_ordered(self):
        from src.core.constants import EmotionalConstants

        assert EmotionalConstants.LOW_CONFIDENCE < EmotionalConstants.MEDIUM_CONFIDENCE
        assert EmotionalConstants.MEDIUM_CONFIDENCE < EmotionalConstants.HIGH_CONFIDENCE

    def test_neutral_score_centered(self):
        from src.core.constants import EmotionalConstants

        assert 0.4 <= EmotionalConstants.NEUTRAL_SCORE <= 0.6


class TestConstantsIntegration:
    def test_all_constants_importable(self):
        from src.core.constants import (
            AudioConstants,
            CacheConstants,
            CircuitBreakerConstants,
            EmbeddingConstants,
            EmotionalConstants,
            MemoryConstants,
            PersonalityConstants,
            SessionConstants,
            TTSConstants,
            VisionConstants,
        )

        assert MemoryConstants is not None
        assert CacheConstants is not None
        assert AudioConstants is not None
        assert TTSConstants is not None
        assert CircuitBreakerConstants is not None
        assert PersonalityConstants is not None
        assert EmbeddingConstants is not None
        assert SessionConstants is not None
        assert VisionConstants is not None
        assert EmotionalConstants is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
