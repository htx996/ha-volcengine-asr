"""Config flow for Volcengine ASR (豆包大模型语音识别).

Adds a UI so the integration can be configured from
Settings -> Devices & Services -> Add Integration, without editing YAML.
"""
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_APP_ID,
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_RESOURCE_ID,
    CONF_SERVICE_URL,
    CONF_LANGUAGE,
    CONF_AUDIO_FORMAT,
    CONF_AUDIO_RATE,
    CONF_AUDIO_BITS,
    CONF_AUDIO_CHANNEL,
    CONF_ENABLE_ITN,
    CONF_ENABLE_PUNC,
    CONF_RESULT_TYPE,
    CONF_SHOW_UTTERANCES,
    CONF_PERFORMANCE_MODE,
    CONF_END_WINDOW_SIZE,
    CONF_FORCE_TO_SPEECH_TIME,
    CONF_LOG_TEXT_CHANGE_ONLY,
    CONF_ENABLE_PERF_LOG,
    CONF_LOG_LEVEL,
    DEFAULT_SERVICE_URL,
    DEFAULT_LANGUAGE,
    DEFAULT_AUDIO_FORMAT,
    DEFAULT_AUDIO_RATE,
    DEFAULT_AUDIO_BITS,
    DEFAULT_AUDIO_CHANNEL,
    DEFAULT_ENABLE_ITN,
    DEFAULT_ENABLE_PUNC,
    DEFAULT_RESULT_TYPE,
    DEFAULT_SHOW_UTTERANCES,
    DEFAULT_PERFORMANCE_MODE,
    DEFAULT_END_WINDOW_SIZE,
    DEFAULT_FORCE_TO_SPEECH_TIME,
    DEFAULT_LOG_TEXT_CHANGE_ONLY,
    DEFAULT_ENABLE_PERF_LOG,
    DEFAULT_LOG_LEVEL,
)

_LOGGER = logging.getLogger(__name__)

# 流式大模型版·时长计费（实测与 API Key 兼容的资源 ID）
DEFAULT_RESOURCE_ID = "volc.bigasr.sauc.duration"

# 高级可选项及其默认值（创建条目时全部落盘，YAML 路径与 UI 路径行为一致）
ADVANCED_DEFAULTS = {
    CONF_SERVICE_URL: DEFAULT_SERVICE_URL,
    CONF_LANGUAGE: DEFAULT_LANGUAGE,
    CONF_AUDIO_FORMAT: DEFAULT_AUDIO_FORMAT,
    CONF_AUDIO_RATE: DEFAULT_AUDIO_RATE,
    CONF_AUDIO_BITS: DEFAULT_AUDIO_BITS,
    CONF_AUDIO_CHANNEL: DEFAULT_AUDIO_CHANNEL,
    CONF_ENABLE_ITN: DEFAULT_ENABLE_ITN,
    CONF_ENABLE_PUNC: DEFAULT_ENABLE_PUNC,
    CONF_RESULT_TYPE: DEFAULT_RESULT_TYPE,
    CONF_SHOW_UTTERANCES: DEFAULT_SHOW_UTTERANCES,
    CONF_PERFORMANCE_MODE: DEFAULT_PERFORMANCE_MODE,
    CONF_END_WINDOW_SIZE: DEFAULT_END_WINDOW_SIZE,
    CONF_FORCE_TO_SPEECH_TIME: DEFAULT_FORCE_TO_SPEECH_TIME,
    CONF_LOG_TEXT_CHANGE_ONLY: DEFAULT_LOG_TEXT_CHANGE_ONLY,
    CONF_ENABLE_PERF_LOG: DEFAULT_ENABLE_PERF_LOG,
    CONF_LOG_LEVEL: DEFAULT_LOG_LEVEL,
}


def _advanced_schema(user_input: dict) -> vol.Schema:
    """Build the advanced-options schema with suggested values."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_LANGUAGE, default=user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
            ): str,
            vol.Optional(
                CONF_ENABLE_ITN,
                default=user_input.get(CONF_ENABLE_ITN, DEFAULT_ENABLE_ITN),
            ): bool,
            vol.Optional(
                CONF_ENABLE_PUNC,
                default=user_input.get(CONF_ENABLE_PUNC, DEFAULT_ENABLE_PUNC),
            ): bool,
            vol.Optional(
                CONF_RESULT_TYPE,
                default=user_input.get(CONF_RESULT_TYPE, DEFAULT_RESULT_TYPE),
            ): vol.In(["single", "full"]),
            vol.Optional(
                CONF_SHOW_UTTERANCES,
                default=user_input.get(CONF_SHOW_UTTERANCES, DEFAULT_SHOW_UTTERANCES),
            ): bool,
            vol.Optional(
                CONF_PERFORMANCE_MODE,
                default=user_input.get(CONF_PERFORMANCE_MODE, DEFAULT_PERFORMANCE_MODE),
            ): bool,
            vol.Optional(
                CONF_END_WINDOW_SIZE,
                default=user_input.get(CONF_END_WINDOW_SIZE, DEFAULT_END_WINDOW_SIZE),
            ): vol.All(vol.Coerce(int), vol.Range(min=100, max=60000)),
            vol.Optional(
                CONF_FORCE_TO_SPEECH_TIME,
                default=user_input.get(
                    CONF_FORCE_TO_SPEECH_TIME, DEFAULT_FORCE_TO_SPEECH_TIME
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60000)),
            vol.Optional(
                CONF_SERVICE_URL,
                default=user_input.get(CONF_SERVICE_URL, DEFAULT_SERVICE_URL),
            ): str,
            vol.Optional(
                CONF_AUDIO_FORMAT,
                default=user_input.get(CONF_AUDIO_FORMAT, DEFAULT_AUDIO_FORMAT),
            ): str,
            vol.Optional(
                CONF_AUDIO_RATE,
                default=user_input.get(CONF_AUDIO_RATE, DEFAULT_AUDIO_RATE),
            ): vol.All(vol.Coerce(int), vol.Range(min=8000, max=48000)),
            vol.Optional(
                CONF_AUDIO_BITS,
                default=user_input.get(CONF_AUDIO_BITS, DEFAULT_AUDIO_BITS),
            ): vol.All(vol.Coerce(int), vol.In([8, 16, 24, 32])),
            vol.Optional(
                CONF_AUDIO_CHANNEL,
                default=user_input.get(CONF_AUDIO_CHANNEL, DEFAULT_AUDIO_CHANNEL),
            ): vol.All(vol.Coerce(int), vol.In([1, 2])),
            vol.Optional(
                CONF_LOG_TEXT_CHANGE_ONLY,
                default=user_input.get(
                    CONF_LOG_TEXT_CHANGE_ONLY, DEFAULT_LOG_TEXT_CHANGE_ONLY
                ),
            ): bool,
            vol.Optional(
                CONF_ENABLE_PERF_LOG,
                default=user_input.get(CONF_ENABLE_PERF_LOG, DEFAULT_ENABLE_PERF_LOG),
            ): bool,
            vol.Optional(
                CONF_LOG_LEVEL,
                default=user_input.get(CONF_LOG_LEVEL, DEFAULT_LOG_LEVEL),
            ): vol.In(["debug", "info", "warning", "error"]),
        }
    )


class VolcengineASRConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Volcengine ASR."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step (API key + resource id)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = (user_input.get(CONF_API_KEY) or "").strip()
            resource_id = (user_input.get(CONF_RESOURCE_ID) or "").strip()
            if not api_key:
                errors[CONF_API_KEY] = "invalid_api_key"
            if not resource_id:
                errors[CONF_RESOURCE_ID] = "invalid_resource_id"

            if not errors:
                await self.async_set_unique_id(api_key)
                self._abort_if_unique_id_configured()
                data = {
                    CONF_API_KEY: api_key,
                    CONF_RESOURCE_ID: resource_id,
                    # 旧版 AppID/Token 体系已下线，留空占位保持兼容
                    CONF_APP_ID: "",
                    CONF_ACCESS_TOKEN: "",
                    **ADVANCED_DEFAULTS,
                }
                return self.async_create_entry(
                    title=user_input.get("name", "豆包语音识别").strip()
                    or "豆包语音识别",
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional("name", default="豆包语音识别"): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(
                        CONF_RESOURCE_ID, default=DEFAULT_RESOURCE_ID
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "apikey_url": "https://console.volcengine.com/speech/new/setting/apikeys",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the advanced options flow."""
        return VolcengineASROptionsFlow()


class VolcengineASROptionsFlow(OptionsFlow):
    """Advanced options for the Volcengine ASR integration."""

    # HA 2025.x+ 的 OptionsFlow.config_entry 是基类只读 property，
    # 由框架在构造后通过 handler/hass 注入；构造器不接收参数。
    def __init__(self) -> None:
        """Initialize options flow."""
        super().__init__()

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the advanced options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {
            **self.config_entry.data,
            **(self.config_entry.options or {}),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=_advanced_schema(current),
        )
