from unittest.mock import MagicMock

import pytest

from utils.choices.choices import BaseChoices


class MyChoices(BaseChoices):
    a = "a", "Choices A"
    b = "b", "Choices B"


class TestBaseChoices:
    @staticmethod
    def test_get_translations():
        # Mocking the BaseTranslator class and its methods
        with pytest.raises(AttributeError):
            MyChoices.get_translations("en")

    @staticmethod
    def test_choices_as_kv_pair():
        # Mocking get_translations method
        MyChoices.get_translations = MagicMock(
            return_value={"a": "Translated Choice A", "b": "Choice B"}
        )

        # Test choices_as_kv_pair for English language
        expected = [
            {"key": "a", "display_name": "Translated Choice A"},
            {"key": "b", "display_name": "Choice B"},
        ]
        assert MyChoices.choices_as_kv_pair("en") == expected

    @staticmethod
    def test_keys():
        # Test keys method
        expected = ["a", "b"]
        assert MyChoices.keys() == expected

    @staticmethod
    def test_get_dictionary():
        # Test get_dictionary method
        expected = {"a": "Choices A", "b": "Choices B"}
        assert MyChoices.get_dictionary() == expected
