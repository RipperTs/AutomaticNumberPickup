# 叫号助手自动取号

需要自己抓取openid和keyword参数, code参数算法已实现无需关注.   

经纬度参考: 35.012981,118.269783 支持模拟定位

## 运行

```shell
python web_main.py

浏览器访问 http://127.0.0.1:5000
```

`main.py` 文件是基础调试版本, 请使用`web_main.py`文件运行


## 打包
```shell
pyinstaller app.spec
```

## 小程序解包
- 解包工具: [KillWxapkg](https://github.com/Ackites/KillWxapkg)

## 小程序码示例
![img.png](img.png)