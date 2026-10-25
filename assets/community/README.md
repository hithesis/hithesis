# 社区入口素材

`qq-group.svg` 由 `community-data.js` 中的官方进群链接生成，保留白底和二维码静区。

重新生成：安装 Python `qrcode` 后，在下载站目录运行
`python3 tools/generate-community-qr.py`。

贡献者姓名与收款码来源记录在 `community-data.js`，原图地址固定到相应仓库提交。
页面使用本站的 WebP 缓存；打开贡献者名单时预加载，切换支付方式时复用已加载图片。

重新生成收款码：安装 Python `Pillow` 和 `zxing-cpp` 后运行
`python3 tools/cache-donation-codes.py`。脚本会核对压缩前后的二维码内容；无法解码的原图只使用无损编码。
