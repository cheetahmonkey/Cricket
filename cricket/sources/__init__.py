from .carter import CarterSource, LocalSubaruSource
from .subaru_cpo import SubaruCpoSource


def build_source(source_config):
    adapter = source_config.get("adapter")
    if adapter == "carter":
        return CarterSource(source_config)
    if adapter == "subaru_cpo":
        return SubaruCpoSource(source_config)
    if adapter == "local_subaru":
        return LocalSubaruSource(source_config)
    raise ValueError("Unknown source adapter: %s" % adapter)
