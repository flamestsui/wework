import logging
import time
import hashlib
import base64
import os
import json
import functools
from typing import Any

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.notify import (
    BaseNotificationService,
    ATTR_MESSAGE,
    ATTR_TITLE,
    ATTR_DATA,
    ATTR_TARGET,
    DOMAIN as NOTIFY_DOMAIN,
)

# 集成唯一标识
DOMAIN = "wework"
# 配置项键名（与config_flow.py一致）
CONF_WEBHOOK = "webhook"

_LOGGER = logging.getLogger(__name__)
DIVIDER = "———————————"


class WeworkNotificationService(BaseNotificationService):
    """企业微信机器人通知服务实现"""

    def __init__(self, webhook: str):
        self._webhook = webhook
        # 提取key（用于文件上传）
        self._key = self._extract_key(webhook)
        _LOGGER.debug(f"企业微信机器人初始化，Webhook: {webhook[:30]}...")

    def _extract_key(self, webhook: str) -> str:
        """从Webhook中提取key（用于文件上传接口）"""
        try:
            return webhook.split("key=")[1].split("&")[0]  # 兼容带其他参数的URL
        except (IndexError, ValueError):
            _LOGGER.warning("Webhook格式异常，可能影响文件上传功能")
            return ""

    def send_message(self, message: str = "", **kwargs):
        """同步发送通知（由异步方法包装）"""
        send_url = self._webhook
        data = kwargs.get(ATTR_DATA) or {}
        msgtype = data.get("type", "text").lower()  # 消息类型（小写处理）
        title = kwargs.get(ATTR_TITLE)
        url = data.get("url", "")
        picurl = data.get("picurl", "")
        imagepath = data.get("imagepath", "")
        filepath = data.get("filepath", "")
        atmoblies = kwargs.get(ATTR_TARGET)  # @指定用户的手机号列表

        # 1. 构建消息内容（按企业微信API格式）
        try:
            if msgtype == "text":
                content = ""
                if title:
                    content += f"{title}\n{DIVIDER}\n"
                content += message
                msg = {
                    "content": content,
                    "mentioned_list": [],
                    "mentioned_mobile_list": atmoblies or []
                }

            elif msgtype == "markdown":
                content = ""
                if title:
                    content += f"{title}\n{DIVIDER}\n"
                content += message
                msg = {"content": content}

            elif msgtype == "image":
                if not imagepath or not os.path.isfile(imagepath):
                    _LOGGER.error("图片路径为空或文件不存在，无法发送图片消息")
                    return
                # 图片转base64和md5
                with open(imagepath, 'rb') as f:
                    image_data = f.read()
                base64_data = base64.b64encode(image_data).decode('utf8')
                fmd5 = hashlib.md5(image_data).hexdigest()
                msg = {"base64": base64_data, "md5": fmd5}

            elif msgtype == "news":
                msg = {
                    "articles": [{
                        "title": title or "通知",
                        "description": message,
                        "url": url,
                        "picurl": picurl
                    }]
                }

            elif msgtype == "file":
                if not self._key:
                    _LOGGER.error("无法提取Webhook中的key，无法上传文件")
                    return
                if not filepath or not os.path.isfile(filepath):
                    _LOGGER.error("文件路径为空或文件不存在，无法发送文件消息")
                    return
                # 上传文件获取media_id
                upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={self._key}&type=file"
                try:
                    with open(filepath, 'rb') as f:
                        multipart_data = MultipartEncoder(
                            fields={'media': (os.path.basename(filepath), f, 'application/octet-stream')}
                        )
                        headers = {'Content-Type': multipart_data.content_type}
                        response = requests.post(
                            upload_url,
                            data=multipart_data,
                            headers=headers,
                            timeout=(20, 180)  # 上传超时设置（连接20s，读取180s）
                        )
                        response.raise_for_status()
                        upload_result = response.json()
                except requests.exceptions.RequestException as e:
                    _LOGGER.error(f"文件上传失败：{str(e)}")
                    return
                if upload_result.get("errcode") != 0:
                    _LOGGER.error(f"文件上传失败：{upload_result.get('errmsg')}")
                    return
                msg = {"media_id": upload_result["media_id"]}

            else:
                _LOGGER.error(f"不支持的消息类型：{msgtype}，请使用 text/markdown/image/news/file")
                return

        except Exception as e:
            _LOGGER.error(f"构建消息失败：{str(e)}")
            return

        # 2. 发送消息请求
        try:
            send_values = {
                "msgtype": msgtype,
                msgtype: msg
            }
            _LOGGER.debug(f"发送消息数据：{send_values}")

            response = requests.post(
                send_url,
                data=json.dumps(send_values),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()

            if result.get("errcode") != 0:
                _LOGGER.error(f"发送失败：{result.get('errmsg', '未知错误')}（错误码：{result.get('errcode')}）")
            else:
                _LOGGER.debug(f"发送成功：{result}")

        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"网络请求失败：{str(e)}")
        except json.JSONDecodeError:
            _LOGGER.error(f"响应格式错误，原始内容：{response.text[:200]}")
        except Exception as e:
            _LOGGER.error(f"发送异常：{str(e)}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """加载配置项并注册服务"""
    _LOGGER.debug("企业微信集成开始加载...")

    # 注册配置更新监听
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # 定义服务处理函数（异步包装同步发送方法）
    async def async_handle_service(call: ServiceCall) -> None:
        webhook = entry.data[CONF_WEBHOOK]
        service = WeworkNotificationService(webhook)
        
        # 提取message并移除重复参数
        message = call.data.get(ATTR_MESSAGE, "")
        other_kwargs = call.data.copy()
        other_kwargs.pop(ATTR_MESSAGE, None)
        
        # 绑定参数并异步执行
        send_func = functools.partial(
            service.send_message,
            message=message,** other_kwargs
        )
        await hass.async_add_executor_job(send_func)

    # 注册服务（调用时使用 notify.wework）
    hass.services.async_register(NOTIFY_DOMAIN, DOMAIN, async_handle_service)
    _LOGGER.debug("企业微信服务注册成功：notify.wework")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置项（移除服务）"""
    hass.services.async_remove(NOTIFY_DOMAIN, DOMAIN)
    _LOGGER.debug("企业微信服务已卸载")
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """配置更新后重新加载服务"""
    await hass.config_entries.async_reload(entry.entry_id)