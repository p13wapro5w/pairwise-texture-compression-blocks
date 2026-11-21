"""块压缩贴图管线的格式选择与对齐工具。

对应十类问题的修复入口：
  endpoint_bits   高质量块压缩：按格式查端点量化位数，暗部渐变需选高位端点格式
  normal_format   法线专用格式：切线空间法线走双通道 BC5，不进 BC1
  block_align     块对齐：尺寸向上取整到 block 的倍数，边缘块不再被拉伸
  mip_order       压缩前生成 mip：先生成 mip 再压缩，避免块误差逐级放大
  srgb_mode       按色彩空间：sRGB 贴图走 sRGB 解码路径，不按线性值压缩
  quality_for     按用途分档：颜色/法线/遮罩各用不同质量参数
  keep_alpha      保留 alpha：带透明通道的贴图只能选 alpha-capable 格式
  filter_for      过滤适配：压缩块上的各向异性采样需做块对齐梯度适配
  atlas_pad        图集 padding：四周留 padding，防止相邻块渗色
  platform_format 按平台选格式：移动端 ASTC，桌面/主机 BC7，避免解码偏色
"""

# 各块压缩格式颜色端点的每通道量化位数。
# BC1/BC2/BC3 颜色端点为 RGB565（R/B 5 位、G 6 位），暗部渐变只能断成几档；
# BC4/BC5 为 8 位单/双通道；BC6H 为 16 位浮点端点（HDR）；
# BC7 端点最高 7 位并带 P 位插值；ASTC 端点最高 8 位。
_ENDPOINT_BITS = {
    "bc1": 5,
    "bc2": 5,
    "bc3": 5,
    "bc4": 8,
    "bc5": 8,
    "bc6h": 16,
    "bc7": 7,
    "astc": 8,
}

# 法线贴图专用格式：切线空间法线只需两个通道，BC5（RG 双通道 8 位端点）
# 不破坏切线空间；禁止把法线塞进 BC1 的三通道低精度端点。
_NORMAL_FORMATS = {
    "normal": "bc5",
    "normal_rg": "bc5",
    "normal_ag": "bc5",
    "bc5n": "bc5",
}

# mip 生成相对压缩的顺序：必须 before——先在原图上 box/高斯降采样，
# 再逐级压缩；after 会把上一级的块误差带进下一级。
_MIP_ORDER = {
    "before": True,
    "after": False,
}

# 按贴图用途分档的压缩质量参数（0~1，越高越慢、失真越小）。
# 颜色类贴图对色阶断裂最敏感，给满档；数据类遮罩可降档省时间。
_QUALITY = {
    "color": 1.0,
    "albedo": 1.0,
    "diffuse": 1.0,
    "ui": 1.0,
    "emissive": 0.9,
    "normal": 0.9,
    "roughness": 0.6,
    "metallic": 0.6,
    "ao": 0.6,
    "height": 0.6,
    "mask": 0.5,
}

# 能保留 alpha 通道的块压缩格式。
# BC1 只有不透明端点（即便旧式 1 位 alpha 也无法表达半透明），
# 半透明边缘必须走 BC2/BC3/BC7/ASTC 这类带独立 alpha 编码的格式。
_ALPHA_FORMATS = frozenset({
    "bc2",
    "bc3",
    "bc7",
    "astc",
    "etc2_rgba",
})

# 各平台的首选块压缩格式。移动端 GPU 对 ASTC 原生支持且色域正确，
# 桌面/主机走 BPTC（BC7）；Web 取兼容性最广的 BC1（S3TC）。
_PLATFORM_FORMATS = {
    "mobile": "astc",
    "android": "astc",
    "ios": "astc",
    "pc": "bc7",
    "desktop": "bc7",
    "windows": "bc7",
    "console": "bc7",
    "web": "bc1",
}

# 每像素位数（bpp）。ASTC 取默认 4x4 footprint 的 8bpp，
# 更大 footprint（5x5、6x6…）会更低，需在调用处按实际尺寸另算。
_BPP = {
    "bc1": 4,
    "bc2": 8,
    "bc3": 8,
    "bc4": 4,
    "bc5": 8,
    "bc6h": 8,
    "bc7": 8,
    "astc": 8,
    "etc2_rgb": 4,
    "etc2_rgba": 8,
}


def endpoint_bits(fmt):
    """高质量块压缩：返回格式的端点每通道量化位数，未知格式报错。"""
    try:
        return _ENDPOINT_BITS[fmt]
    except KeyError:
        raise ValueError("unknown block format: %r" % (fmt,))


def normal_format(kind):
    """法线专用格式：切线空间法线映射到双通道 BC5。"""
    try:
        return _NORMAL_FORMATS[kind]
    except KeyError:
        raise ValueError("unknown normal texture kind: %r" % (kind,))


def block_align(size, block):
    """块对齐：把尺寸向上取整到 block 的倍数，消除被拉伸的边缘半块。"""
    if block <= 0:
        raise ValueError("block must be positive, got %r" % (block,))
    size = int(size)
    return ((size + block - 1) // block) * block


def mip_order(order):
    """压缩前生成 mip：'before' 返回 True，'after' 返回 False。"""
    try:
        return _MIP_ORDER[order]
    except KeyError:
        raise ValueError("mip order must be 'before' or 'after', got %r" % (order,))


def srgb_mode(srgb):
    """按色彩空间：sRGB 贴图返回 'srgb'，线性数据返回 'linear'。"""
    if isinstance(srgb, str):
        normalized = srgb.lower()
        if normalized in ("srgb", "gamma"):
            return "srgb"
        if normalized == "linear":
            return "linear"
        raise ValueError("unknown color space: %r" % (srgb,))
    return "srgb" if srgb else "linear"


def quality_for(purpose):
    """按用途分档：返回该用途贴图的压缩质量参数（0~1）。"""
    try:
        return _QUALITY[purpose]
    except KeyError:
        raise ValueError("unknown texture purpose: %r" % (purpose,))


def keep_alpha(fmt):
    """保留 alpha：判断格式是否能编码连续 alpha 通道。"""
    return fmt in _ALPHA_FORMATS


def filter_for(aniso):
    """过滤适配：返回是否在压缩块上启用块对齐梯度的各向异性过滤。

    各向异性级数为真值（True 或 >=1）时启用适配，采样梯度按 4x4 块
    对齐后再取纹理，避免斜视角跨块插值产生条纹；0/False 关闭。
    """
    if isinstance(aniso, bool):
        return aniso
    return int(aniso) > 0


def atlas_pad(size, pad):
    """图集 padding：返回四周各留 pad 像素后的总尺寸（size + 2*pad）。"""
    if pad < 0:
        raise ValueError("pad must be non-negative, got %r" % (pad,))
    return int(size) + 2 * int(pad)


def platform_format(platform):
    """按平台选格式：移动 ASTC、桌面/主机 BC7、Web BC1，未知平台报错。"""
    try:
        return _PLATFORM_FORMATS[platform]
    except KeyError:
        raise ValueError("unknown platform: %r" % (platform,))


def blocks(size, block):
    """块数量：覆盖 size 所需的 block 数（向上取整，含边缘半块）。"""
    if block <= 0:
        raise ValueError("block must be positive, got %r" % (block,))
    return (int(size) + block - 1) // block


def edge(size, block):
    """块边缘判定：size 不是 block 的整数倍时存在被填充的边缘块。"""
    if block <= 0:
        raise ValueError("block must be positive, got %r" % (block,))
    return int(size) % block != 0


def clamp01(value):
    """归一钳制：把标量夹到 [0, 1] 并以浮点返回。"""
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def key(tex_id):
    """贴图键：生成缓存/图集用的稳定字符串键。"""
    return "t:%s" % (tex_id,)


def bpp(fmt):
    """每像素位数：返回块压缩格式的 bpp，未知格式报错。"""
    try:
        return _BPP[fmt]
    except KeyError:
        raise ValueError("unknown block format: %r" % (fmt,))
