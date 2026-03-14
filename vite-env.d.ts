/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ZHIPU_API_KEY: string
  readonly VITE_GEMINI_API_KEY: string
  readonly VITE_API_KEY: string
  readonly VITE_AI_PROVIDER: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
