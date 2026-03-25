import { existsSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import { HOME } from './paths.js';
import { Config } from './config.js';

const MARKER_START = '# >>> codex-bedrock >>>';
const MARKER_END = '# <<< codex-bedrock <<<';

export function shellIntegrationBlock(config: Config): string {
  return `${MARKER_START}
export OPENAI_API_KEY="${config.apiKey}"

codex() {
  if ! lsof -ti:${config.port} > /dev/null 2>&1; then
    echo "Starting codex-bedrock proxy..."
    codex-bedrock start --profile "${config.awsProfile}" --region "${config.awsRegion}" >/tmp/codex-bedrock.log 2>&1 &
    for i in $(seq 1 15); do
      curl -s http://127.0.0.1:${config.port}/health > /dev/null 2>&1 && break
      sleep 1
    done
  fi
  command codex "$@"
}
${MARKER_END}`;
}

export function detectShellRc(): string | null {
  const shell = process.env.SHELL ?? '';
  const candidates: string[] = [];
  if (shell.includes('zsh')) candidates.push(join(HOME, '.zshrc'));
  else if (shell.includes('bash')) candidates.push(join(HOME, '.bashrc'), join(HOME, '.bash_profile'));
  else if (shell.includes('fish')) candidates.push(join(HOME, '.config', 'fish', 'config.fish'));
  return candidates.find(existsSync) ?? null;
}

export function injectShellIntegration(rcFile: string, config: Config): void {
  let content = existsSync(rcFile) ? readFileSync(rcFile, 'utf-8') : '';

  // Remove existing block if present
  const startIdx = content.indexOf(MARKER_START);
  const endIdx = content.indexOf(MARKER_END);
  if (startIdx !== -1 && endIdx !== -1) {
    content = content.slice(0, startIdx) + content.slice(endIdx + MARKER_END.length);
  }

  content = content.trimEnd() + '\n\n' + shellIntegrationBlock(config) + '\n';
  writeFileSync(rcFile, content);
}

export function removeShellIntegration(rcFile: string): void {
  if (!existsSync(rcFile)) return;
  let content = readFileSync(rcFile, 'utf-8');
  const startIdx = content.indexOf(MARKER_START);
  const endIdx = content.indexOf(MARKER_END);
  if (startIdx !== -1 && endIdx !== -1) {
    content = content.slice(0, startIdx) + content.slice(endIdx + MARKER_END.length);
    writeFileSync(rcFile, content.trimEnd() + '\n');
  }
}
