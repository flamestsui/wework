import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# 配置项键名（与__init__.py保持一致）
CONF_WEBHOOK = "webhook"  # 企业微信机器人Webhook地址


@config_entries.HANDLERS.register(DOMAIN)
class WeworkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """企业微信机器人配置流处理类"""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """处理用户UI配置步骤"""
        errors = {}

        if user_input is not None:
            # 验证Webhook不为空且包含"key="（企业微信Webhook格式要求）
            webhook = user_input[CONF_WEBHOOK].strip()
            if not webhook:
                errors[CONF_WEBHOOK] = "missing_webhook"
            elif "key=" not in webhook:
                errors[CONF_WEBHOOK] = "invalid_webhook"  # 格式错误
            else:
                # 用Webhook作为唯一标识（避免重复配置）
                await self.async_set_unique_id(webhook)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="企业微信机器人",
                    data={CONF_WEBHOOK: webhook}
                )

        # 显示配置表单（UI界面）
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_WEBHOOK, msg="请输入企业微信机器人Webhook地址"): str,
            }),
            errors=errors,
            description_placeholders={
                "hint": "Webhook地址格式示例：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
            }
        )