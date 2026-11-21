# pairwise-texture-compression-blocks

贴图在暗部出现 4x4 的方块，BC1 的端点量化只有 5/6 位，暗部渐变直接断成几档；法线贴图也用 BC1 压，切线空间被破坏，光照出现斑块；压缩块按 4x4 对齐，非 4 倍数尺寸的边缘块被拉伸；先压缩再生成 mip，每级都在放大块误差；sRGB 贴图按线性值压缩，暗部色阶被压平；压缩质量参数写死，颜色贴图和遮罩贴图用同一档；带 alpha 的贴图用了不保留 alpha 的格式，半透明边缘变成硬边；各向异性过滤在压缩块上采样，斜视角出现条纹；图集没有留 padding，相邻块的颜色渗到边缘；不同平台用了同一套压缩格式，移动端解码后颜色偏绿。render/texture_compression_blocks.py 是核心，tests/test_texture_compression_blocks.py 15个红。要修的是：高质量块压缩；法线专用格式；块对齐；压缩前生成 mip；按色彩空间；按用途分档；保留 alpha；过滤适配；图集 padding；按平台选格式。

## 运行

```bash
python -m pytest tests -q
```

初始状态：15 个用例失败。修复实现使全部用例通过，不要修改 `tests/` 下的测试。

子方向：见平台；任务类型：Bugfix；语言/框架：Python 3, pytest；环境可复现等级：无外部依赖。
