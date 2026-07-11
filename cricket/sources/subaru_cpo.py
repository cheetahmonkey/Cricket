from .base import SourceAdapter


class SubaruCpoSource(SourceAdapter):
    def source_defaults(self, url):
        defaults = super().source_defaults(url)
        defaults["cpo"] = True
        return defaults
