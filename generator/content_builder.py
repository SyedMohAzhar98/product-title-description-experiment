def build_title(product, config):
    return config["title_format"].format(
        title=product["name"],
        fabric=product.get("fabric", ""),
        type=product.get("type", "")
    )

def build_subtitle(product, config):
    return config.get("subtitle_format", "").format(
        fabric=product.get("fabric", ""),
        type=product.get("type", "")
    )
