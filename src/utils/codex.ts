import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname } from 'path';
import { CODEX_CONFIG } from './paths.js';
import { Config } from './config.js';

const MARKER_START = '# >>> codex-bedrock >>>';
const MARKER_END = '# <<< codex-bedrock <<<';

function codexConfigBlock(config: Config): string {
  return `${MARKER_START}
model = "gpt-5.4"
openai_base_url = "http://127.0.0.1:${config.port}/v1"
model_context_window = 200000
${MARKER_END}`;
}

export function patchCodexConfig(config: Config): void {
  mkdirSync(dirname(CODEX_CONFIG), { recursive: true });
  let content = existsSync(CODEX_CONFIG) ? readFileSync(CODEX_CONFIG, 'utf-8') : '';

  // Remove existing block
  const startIdx = content.indexOf(MARKER_START);
  const endIdx = content.indexOf(MARKER_END);
  if (startIdx !== -1 && endIdx !== -1) {
    content = content.slice(0, startIdx) + content.slice(endIdx + MARKER_END.length);
  }

  content = content.trimEnd() + '\n\n' + codexConfigBlock(config) + '\n';
  writeFileSync(CODEX_CONFIG, content);
}

export function unpatchCodexConfig(): void {
  if (!existsSync(CODEX_CONFIG)) return;
  let content = readFileSync(CODEX_CONFIG, 'utf-8');
  const startIdx = content.indexOf(MARKER_START);
  const endIdx = content.indexOf(MARKER_END);
  if (startIdx !== -1 && endIdx !== -1) {
    content = content.slice(0, startIdx) + content.slice(endIdx + MARKER_END.length);
    writeFileSync(CODEX_CONFIG, content.trimEnd() + '\n');
  }
}

export async function isCodexInstalled(): Promise<boolean> {
  const { execa } = await import('execa');
  try {
    await execa('codex', ['--version']);
    return true;
  } catch {
    return false;
  }
}
