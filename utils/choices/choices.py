from django.db import models


class BaseChoices(models.TextChoices):
    """
    BaseChoices class representing a base for choice sets in Django models.
    It provides methods for translations and handling choices in different languages.
    """

    @classmethod
    def choices_as_kv_pair(cls, lang=None):
        """
        Returns choices as key-value pairs with translated display names.
        If a language is specified, retrieves translated choices; else, returns choices in their original form.
        """
        if lang:
            translations: dict = cls.get_translations(lang)
            return [
                {"key": key, "display_name": translations.get(key, value)}
                for key, value in cls.choices
            ]

        return [{"key": key, "display_name": value} for key, value in cls.choices]

    @classmethod
    def keys(cls):
        """
        Returns the keys of choices.
        """
        return [key for key, _ in cls.choices]

    @classmethod
    def get_dictionary(cls) -> dict:
        """
        Returns choices as a dictionary.
        """
        _dict = {}
        for key, value in cls.choices:
            _dict[key] = value
        return _dict
