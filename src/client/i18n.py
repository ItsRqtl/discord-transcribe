"""
Internationalization and localization utilities.
"""

from typing import Union

import discord
from pyi18n import PyI18n
from pyi18n.loaders import PyI18nYamlLoader


class I18n:
    """
    Internationalization and localization class.
    Provides a simple interface to get translated strings.
    """

    locales = ("en-US", "zh-TW", "zh-CN")
    i18n_instance = PyI18n(locales, loader=PyI18nYamlLoader("locales", namespaced=True))
    i18n_get = i18n_instance.gettext

    @classmethod
    def get(
        cls,
        key: str,
        language: Union[str, discord.ApplicationContext, discord.Interaction] = "en-US",
        **kwargs,
    ) -> str:
        """
        Get a translated string.

        :param key: The key of the string.
        :type key: str
        :param language: The language to get the string in.
        :type language: str | discord.ApplicationContext | discord.Interaction
        :param kwargs: The arguments to format the string with.
        :type kwargs: dict

        :return: The translated string.
        :rtype: str
        """
        if isinstance(language, (discord.ApplicationContext, discord.Interaction)):
            language = language.locale or language.guild_locale
        if not isinstance(language, str) or language not in cls.locales:
            language = "en-US"
        return cls.i18n_get(language, key, **kwargs)

    @classmethod
    def get_all(cls, key: str, **kwargs) -> dict:
        """
        Get all translated strings for a key.

        :param key: The key of the string.
        :type key: str
        :param kwargs: The arguments to format the string with.
        :type kwargs: dict

        :return: The translated strings.
        :rtype: dict
        """
        return {locale: cls.get(key, locale, **kwargs) for locale in cls.locales}


def slash_command(identifier: str, **kwargs):
    """
    Decorator that registers a slash command.

    :param identifier: The identifier of the locale for the command.
    :type identifier: str
    """
    kwargs["name"] = I18n.get(f"slash.{identifier}.name")
    kwargs["name_localizations"] = I18n.get_all(f"slash.{identifier}.name")
    kwargs["description"] = I18n.get(f"slash.{identifier}.description")
    kwargs["description_localizations"] = I18n.get_all(f"slash.{identifier}.description")
    return discord.application_command(cls=discord.SlashCommand, **kwargs)


def option(identifier: str, parameter_name: str, **kwargs):
    """
    Decorator that registers an option for a slash command.

    :param identifier: The identifier of the locale for the option.
    :type identifier: str
    :param parameter_name: The name of the parameter.
    :type parameter_name: str
    """
    kwargs["name"] = I18n.get(f"slash.{identifier}.option.{parameter_name}.name")
    kwargs["name_localizations"] = I18n.get_all(f"slash.{identifier}.option.{parameter_name}.name")
    kwargs["description"] = I18n.get(f"slash.{identifier}.option.{parameter_name}.description")
    kwargs["description_localizations"] = I18n.get_all(
        f"slash.{identifier}.option.{parameter_name}.description"
    )
    kwargs["parameter_name"] = parameter_name
    return discord.option(**kwargs)


def message_command(identifier: str, **kwargs):
    """
    Decorator that registers a message command.

    :param identifier: The identifier of the locale for the command.
    :type identifier: str
    """
    kwargs["name"] = I18n.get(f"message.{identifier}.name")
    kwargs["name_localizations"] = I18n.get_all(f"message.{identifier}.name")
    return discord.application_command(cls=discord.MessageCommand, **kwargs)


def user_command(identifier: str, **kwargs):
    """
    Decorator that registers a user command.

    :param identifier: The identifier of the locale for the command.
    :type identifier: str
    """
    kwargs["name"] = I18n.get(f"user.{identifier}.name")
    kwargs["name_localizations"] = I18n.get_all(f"user.{identifier}.name")
    return discord.application_command(cls=discord.UserCommand, **kwargs)
