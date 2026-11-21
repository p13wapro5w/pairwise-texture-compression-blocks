import math

def endpoint_bits(fmt):
    """高质量块压缩。"""
    raise NotImplementedError("TODO: endpoint_bits")

def normal_format(kind):
    """法线专用格式。"""
    raise NotImplementedError("TODO: normal_format")

def block_align(size, block):
    """块对齐。"""
    raise NotImplementedError("TODO: block_align")

def mip_order(order):
    """压缩前生成 mip。"""
    raise NotImplementedError("TODO: mip_order")

def srgb_mode(srgb):
    """按色彩空间。"""
    raise NotImplementedError("TODO: srgb_mode")

def quality_for(purpose):
    """按用途分档。"""
    raise NotImplementedError("TODO: quality_for")

def keep_alpha(fmt):
    """保留 alpha。"""
    raise NotImplementedError("TODO: keep_alpha")

def filter_for(aniso):
    """过滤适配。"""
    raise NotImplementedError("TODO: filter_for")

def atlas_pad(size, pad):
    """图集 padding。"""
    raise NotImplementedError("TODO: atlas_pad")

def platform_format(platform):
    """按平台选格式。"""
    raise NotImplementedError("TODO: platform_format")

def blocks(size, block):
    """块数量。"""
    raise NotImplementedError("TODO: blocks")

def edge(size, block):
    """块边缘判定。"""
    raise NotImplementedError("TODO: edge")

def clamp01(value):
    """归一钳制。"""
    raise NotImplementedError("TODO: clamp01")

def key(tex_id):
    """贴图键。"""
    raise NotImplementedError("TODO: key")

def bpp(fmt):
    """每像素位数。"""
    raise NotImplementedError("TODO: bpp")
