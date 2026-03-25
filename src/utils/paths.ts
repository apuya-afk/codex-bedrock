import { homedir } from 'os';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export const HOME = homedir();
export const CODEX_BEDROCK_DIR = join(HOME, '.codex-bedrock');
export const CONFIG_FILE = join(CODEX_BEDROCK_DIR, 'config.json');
export const PID_FILE = join(CODEX_BEDROCK_DIR, 'proxy.pid');
export const LOG_FILE = join(CODEX_BEDROCK_DIR, 'proxy.log');
export const VENV_DIR = join(CODEX_BEDROCK_DIR, 'venv');
export const PROXY_SRC = join(__dirname, '..', '..', 'proxy');
export const CODEX_CONFIG = join(HOME, '.codex', 'config.toml');
