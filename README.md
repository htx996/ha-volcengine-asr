# 豆包语音识别（Volcengine ASR for Home Assistant）

将火山引擎「豆包大模型语音识别」接入 Home Assistant 语音助手的中文语音转文字（STT）组件。

基于 [zhouruhui/volcengine-asr-ha](https://github.com/zhouruhui/volcengine-asr-ha) 的社区重写版（原上游 `manus-team/ha-volcengine-asr` 仓库已不存在）。

## ✨ 特性

- **图形化配置界面**：设置 → 设备与服务 → 添加集成 → 「豆包语音识别」，API Key 表单化填写，无需手改 YAML
- **新版 API Key 鉴权**：使用火山引擎官方推荐的 `x-api-key` 鉴权（旧版 AppID + Access Token 体系已被火山下线，一律返回 401 `grant not found`）
- **流式大模型识别**：`wss://openspeech.bytedance.com/api/v3/sauc/bigmodel`，资源 ID `volc.bigasr.sauc.duration`
- **双语界面**：简体中文 / English 配置向导与高级选项
- **高级选项全部可视化**：语言、标点、ITN、VAD 结束窗口、强制语音判定、性能模式、日志级别等

## 🔧 相对上游的重要修复

1. **鉴权体系迁移**：AppID + Access Token → API Key（`x-api-key`），旧体系实测全部 401
2. **接收循环重写**：修复发完音频后只等 2 秒导致的间歇性 `no recognized text`；现循环接收直至最终结果 / 连接关闭 / 文本稳定（上限 8 秒）
3. **流式传输期间不再轮询 receive()**：修复 aiohttp `wait_for` 取消接收导致结果丢失的问题
4. **服务器主动关闭连接的正确处理**：`autoping=False` + `ClientConnectionResetError` 容错，消除 `Cannot write to closing transport` 报错
5. **WAV 文件头剥离**：HA 以 WAV 流式传音频，自动剥离 RIFF 头后再以 raw PCM 送入
6. **字节级诊断日志**：`ASR DIAG` 系列日志（首块十六进制、音量统计、每条 WS 消息），排障一目了然

## 📦 安装

### 方式一：HACS（推荐）

1. 在 HACS 中添加自定义仓库：`https://github.com/qian2023qian/ha-volcengine-asr`（类别：集成）
2. 搜索「豆包语音识别」安装，重启 Home Assistant

### 方式二：手动安装

将 `custom_components/volcengine_asr` 目录复制到 Home Assistant 配置目录的 `custom_components/` 下，重启 Home Assistant。

## ⚙️ 配置

1. **设置 → 设备与服务 → 添加集成**，搜索「豆包语音识别」
2. 填写：
   - **API Key**：在[火山引擎语音技术控制台 → API Key 管理](https://console.volcengine.com/speech/new/setting/apikeys)创建
   - **资源 ID**：默认 `volc.bigasr.sauc.duration`（流式大模型·时长计费版）
3. 保存后在 **设置 → 语音助手 → 配置管道** 中把语音转文本引擎选为「豆包语音识别」
4. 点集成的 ⚙️ 齿轮可随时调整高级选项（VAD、标点、日志等）

> 旧版 YAML 配置（`configuration.yaml` 中的 `volcengine_asr:` 块）仍被兼容支持，但推荐使用 UI 配置。

## ❓ 常见问题

- **识别慢**：默认 VAD 结束窗口 2000ms，语音结束后约 2 秒出结果；可在高级选项中调小
- **听不到识别文字**：先看 HA 日志中的 `ASR DIAG stream summary`，`avg_level < 1%` 说明麦克风输入是静音（硬件问题），`3-25%` 为正常语音
- **费用**：`volc.bigasr.sauc.duration` 为时长计费，按识别音频时长计费；火山引擎新用户通常有免费额度

## 📄 许可

MIT License。基于 zhouruhui/volcengine-asr-ha（MIT）重写。
