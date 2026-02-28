import { create } from 'zustand';

const STORAGE_KEY = 'audio_transcriber_config';

const DEFAULT_CONFIG = {
  provider: 'gemini',
  model: 'gemini-3-flash-preview',
  baseUrl: '',
  apiKey: '',
  enableDiarization: false,
};

const PROVIDER_DEFAULTS = {
  gemini: {
    displayName: '⭐ Gemini (Google) - 内置',
    model: 'gemini-3-flash-preview',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai',
    link: 'https://aistudio.google.com/apikey',
    serverKey: true,
  },
  aliyun: {
    displayName: '阿里云 (通义听悟)',
    model: 'qwen-audio-turbo',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    link: 'https://bailian.console.aliyun.com/',
  },
  zhipu: {
    displayName: '智谱 AI (GLM)',
    model: 'glm-4-flash',
    baseUrl: '',
    link: 'https://bigmodel.cn/invite?invite_code=6N4G5H',
    isZhipuSDK: true,
  },
  modelscope: {
    displayName: 'ModelScope (魔搭)',
    model: 'iic/SenseVoiceSmall',
    baseUrl: 'https://api-inference.modelscope.ai/v1',
    link: 'https://www.modelscope.cn/my/myaccesstoken',
  },
  custom: {
    displayName: '自定义 (OpenAI / Local)',
    model: '',
    baseUrl: 'https://api.example.com/v1',
  },
};

function loadConfig() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return { ...DEFAULT_CONFIG, ...JSON.parse(saved) };
  } catch (e) { /* ignore */ }
  return { ...DEFAULT_CONFIG };
}

function saveConfig(config) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  } catch (e) { /* ignore */ }
}

export const useConfigStore = create((set, get) => ({
  ...loadConfig(),

  setProvider: (provider) => {
    const defaults = PROVIDER_DEFAULTS[provider] || PROVIDER_DEFAULTS.custom;
    const update = { provider, model: defaults.model, baseUrl: defaults.baseUrl };
    set(update);
    saveConfig({ ...get(), ...update });
  },

  setField: (field, value) => {
    set({ [field]: value });
    const next = { ...get(), [field]: value };
    saveConfig(next);
  },

  resetConfig: () => {
    set({ ...DEFAULT_CONFIG });
    saveConfig(DEFAULT_CONFIG);
  },

  getUploadConfig: () => {
    const { provider, model, baseUrl, apiKey, enableDiarization } = get();
    return { provider, model, baseUrl, apiKey, enableDiarization };
  },
}));

export { PROVIDER_DEFAULTS };
