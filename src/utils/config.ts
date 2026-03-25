import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { CONFIG_FILE, CODEX_BEDROCK_DIR } from './paths.js';

export interface Config {
  awsProfile: string;
  awsRegion: string;
  port: number;
  apiKey: string;
  models: {
    flagship: string;
    balanced: string;
    fast: string;
  };
}

const DEFAULTS: Config = {
  awsProfile: 'default',
  awsRegion: 'us-east-1',
  port: 51822,
  apiKey: '',
  models: {
    flagship: 'us.anthropic.claude-opus-4-6-v1',
    balanced: 'us.anthropic.claude-sonnet-4-6',
    fast: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
  },
};

export function loadConfig(): Config {
  if (!existsSync(CONFIG_FILE)) return { ...DEFAULTS };
  return { ...DEFAULTS, ...JSON.parse(readFileSync(CONFIG_FILE, 'utf-8')) };
}

export function saveConfig(config: Config): void {
  mkdirSync(CODEX_BEDROCK_DIR, { recursive: true });
  writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}
