import codecs
import os

from os import path

I18N_PATH = "i18n"
DEFAULT_LANG = "en"


class I18n:
    def __init__(self, langcode=None, path=None):
        if path is None:
            path = I18N_PATH

        if langcode is None:
            langcode = DEFAULT_LANG
        self.translations = {}
        import os
        for file in os.listdir(I18N_PATH):
            if file.endswith(".i18n"):
                fname = file.split(".")
                self.translations[fname[0]] = Translation(fname[0], file, path)
        self.checkvalidlanguage(langcode)
        self._langcode = langcode

    def get(self, str, langcode=None):
        if langcode is None:
            langcode = self._langcode
        self.checkvalidlanguage(langcode)
        return self.translations[langcode].get(str)

    def setlang(self, langcode):
        self.checkvalidlanguage(langcode)
        self._langcode = langcode

    def checkvalidlanguage(self, langcode):
        if langcode not in self.translations:
            raise TranslationNotFoundException(langcode)


class Translation:
    def __init__(self, code, file, path=None):
        if path is None:
            path = I18N_PATH
        self.code = code
        self.file = file
        self.alltext = self.read_from_file(path)

    def read_from_file(self, path):
        file = codecs.open(path + "/" + self.code + ".i18n", 'r',
                           encoding='utf8')
        data = dict(line.split(":", 1) for line in file)
        file.close()
        return data

    def get(self, text):
        if text not in self.alltext:
            raise StringNotFoundException(text, self)

        return self.alltext[text].replace("\n", "").replace("\r", "").strip()


class TranslationException(Exception):
    pass


class TranslationNotFoundException(TranslationException):
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return "Translation not found: {}".format(self.code)


class StringNotFoundException(TranslationException):
    def __init__(self, string, translation):
        self.string = string
        self.translation = translation

    def __str__(self):
        return "Could not find '{}' in translation {}".format(self.string,
                                                              self.translation.code)
