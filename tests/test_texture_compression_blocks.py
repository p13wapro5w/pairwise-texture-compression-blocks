import pytest
import math
from render import texture_compression_blocks as mod

CASES = [
    ("bits", 'm.endpoint_bits("bc1") == 5'),
    ("normal", 'm.normal_format("normal") == "bc5"'),
    ("align", 'm.block_align(101, 4) == 104'),
    ("mip", 'm.mip_order("before") is True'),
    ("srgb", 'm.srgb_mode(True) == "srgb"'),
    ("quality", 'm.quality_for("color") == 1.0'),
    ("alpha", 'm.keep_alpha("bc1") is False'),
    ("filter", 'm.filter_for(True) is True'),
    ("pad", 'm.atlas_pad(10, 2) == 14'),
    ("platform", 'm.platform_format("mobile") == "astc"'),
    ("blocks", 'm.blocks(9, 4) == 3'),
    ("edge", 'm.edge(9, 4) is True'),
    ("clamp", 'm.clamp01(1.2) == 1.0'),
    ("key", 'm.key(2) == "t:2"'),
    ("bpp", 'm.bpp("bc1") == 4')
]

@pytest.mark.parametrize("name,expr", CASES, ids=[c[0] for c in CASES])
def test_contract(name, expr):
    assert eval(expr, {"m": mod, "approx": pytest.approx, "math": math})
