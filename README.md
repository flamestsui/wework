# 企业微信机器人通知（Home Assistant 集成）

一个用于 Home Assistant 的企业微信机器人通知集成，支持多种消息类型发送，包括文本、Markdown、图片、新闻和文件。

## 功能特点

- 支持多种消息类型：文本、Markdown、图片、新闻、文件
- 支持消息标题和内容分隔显示
- 支持 @ 指定用户（通过手机号）
- 简单易用的配置流程
- 完整的错误日志记录

## 安装方法

### 手动安装

1. 下载本项目代码

2. 将

   ```
   custom_components/wework
   ```

   目录复制到 Home Assistant 的

   ```
   custom_components
   ```

   目录下

   - 通常路径为：`~/.homeassistant/custom_components/`（不同系统可能略有差异）

3. 重启 Home Assistant

## 配置步骤

1. 在企业微信中创建群机器人，获取其 Webhook 地址
   - 打开企业微信群聊 → 群设置 → 群机器人 → 添加机器人 → 复制 Webhook 地址
   - 格式示例：`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxx`
2. 在 Home Assistant 中配置集成
   - 进入 Home Assistant 管理界面 → 配置 → 设备与服务 → 集成 → 添加集成
   - 搜索 `企业微信机器人通知` 并选择
   - 在弹出的表单中输入获取到的 Webhook 地址，点击提交

## 使用说明

配置完成后，可通过调用服务 `notify.wework` 发送通知，支持以下参数：

| 参数名    | 类型   | 说明                                                  |
| --------- | ------ | ----------------------------------------------------- |
| `message` | 字符串 | 消息内容（必填）                                      |
| `title`   | 字符串 | 消息标题（可选，会显示在内容上方并添加分隔线）        |
| `target`  | 列表   | 需 @ 的用户手机号列表（可选，例如 `["13800138000"]`） |
| `data`    | 字典   | 消息类型及附加参数（可选，默认发送文本消息）          |

### `data` 参数说明

`data` 字典用于指定消息类型及对应参数，其中 `type` 字段指定消息类型，支持以下值：

| 类型       | 说明              | 额外参数                                              |
| ---------- | ----------------- | ----------------------------------------------------- |
| `text`     | 文本消息（默认）  | 无                                                    |
| `markdown` | Markdown 格式消息 | 无（支持企业微信兼容的 Markdown 语法）                |
| `image`    | 图片消息          | `imagepath`：本地图片路径（需 Home Assistant 可访问） |
| `news`     | 新闻消息          | `url`：点击新闻跳转的链接；`picurl`：新闻配图链接     |
| `file`     | 文件消息          | `filepath`：本地文件路径（需 Home Assistant 可访问）  |

## 示例

### 1. 发送文本消息

```yaml
service: notify.wework
data:
  message: "这是一条来自 Home Assistant 的文本通知"
  title: "系统通知"
  target: ["13800138000"]  # @指定用户
```

### 2. 发送 Markdown 消息

```yaml
service: notify.wework
data:
  message: "**重要通知**\n\n温度已超过阈值：26℃"
  title: "环境监测告警"
  data:
    type: "markdown"
```

### 3. 发送图片消息

```yaml
service: notify.wework
data:
  message: "客厅摄像头抓拍"  # 图片消息中该字段无效，仅用于兼容
  data:
    type: "image"
    imagepath: "/config/www/snapshots/living_room.jpg"  # 本地图片路径
```

### 4. 发送新闻消息

```yaml
service: notify.wework
data:
  message: "今日天气晴，气温 25℃"
  title: "每日天气报告"
  data:
    type: "news"
    url: "https://example.com/weather"  # 点击跳转链接
    picurl: "https://example.com/weather.jpg"  # 配图链接
```

### 5. 发送文件消息

```yaml
service: notify.wework
data:
  message: "月度能耗报告"  # 文件消息中该字段无效，仅用于兼容
  data:
    type: "file"
    filepath: "/config/reports/energy_202405.pdf"  # 本地文件路径
```

## 注意事项

- 图片和文件路径需为 Home Assistant 可访问的本地路径（建议使用相对路径，如 `/config/` 下的文件）
- 企业微信机器人有消息发送频率限制，请勿频繁发送
- 文件大小限制：普通文件不超过 20MB，图片不超过 2MB
- Markdown 语法支持范围参考 [企业微信官方文档](https://work.weixin.qq.com/api/doc/90000/90135/91770)

## 常见问题

1. **发送失败？**
   - 检查 Webhook 地址是否正确（需包含 `key=`）
   - 检查网络连接（Home Assistant 需能访问 `qyapi.weixin.qq.com`）
   - 查看 Home Assistant 日志（搜索 `wework` 关键词）获取详细错误信息
2. **文件 / 图片发送失败？**
   - 确认文件路径正确且文件存在
   - 确认文件大小未超过限制
   - 检查 Webhook 中的 key 是否有效（文件上传依赖 key 提取）

## 相关链接

- [企业微信机器人官方文档](https://work.weixin.qq.com/api/doc/90000/90135/91770)
- [Home Assistant 通知服务文档](https://www.home-assistant.io/integrations/notify/)
