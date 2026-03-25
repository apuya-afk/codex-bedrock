import { existsSync, readFileSync, writeFileSync } from 'fs';
import { execa } from 'execa';
import { PID_FILE, VENV_DIR } from './paths.js';
import { Config } from './config.js';

export function readPid(): number | null {
  if (!existsSync(PID_FILE)) return null;
  const pid = parseInt(readFileSync(PID_FILE, 'utf-8').trim(), 10);
  return isNaN(pid) ? null : pid;
}

export function isRunning(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

export function proxyStatus(): { running: boolean; pid: number | null } {
  const pid = readPid();
  if (pid === null) return { running: false, pid: null };
  return { running: isRunning(pid), pid };
}

export async function installProxy(): Promise<void> {
  const python = await resolvePython();
  await execa(python, ['-m', 'venv', VENV_DIR], { stdio: 'inherit' });
  const pip = `${VENV_DIR}/bin/pip`;
  await execa(pip, ['install', '-e', '.', '--quiet'], {
    cwd: `${process.env.HOME}/.codex-bedrock/../`,
    stdio: 'inherit',
  });
}

export function buildEnv(config: Config): NodeJS.ProcessEnv {
  return {
    ...process.env,
    AWS_PROFILE: config.awsProfile,
    AWS_REGION: config.awsRegion,
    AWS_DEFAULT_REGION: config.awsRegion,
    CODEX_BEDROCK_API_KEY: config.apiKey,
    PORT: String(config.port),
    HOST: '127.0.0.1',
    ALLOWED_ORIGINS: 'null',
    CODEX_BEDROCK_MODEL_FLAGSHIP: config.models.flagship,
    CODEX_BEDROCK_MODEL_BALANCED: config.models.balanced,
    CODEX_BEDROCK_MODEL_FAST: config.models.fast,
  };
}

export async function resolvePython(): Promise<string> {
  for (const cmd of ['python3', 'python']) {
    try {
      const { stdout } = await execa(cmd, ['--version']);
      const match = stdout.match(/Python (\d+)\.(\d+)/);
      if (match && (parseInt(match[1]) > 3 || (parseInt(match[1]) === 3 && parseInt(match[2]) >= 11))) {
        return cmd;
      }
    } catch { /* try next */ }
  }
  throw new Error('Python 3.11+ is required. Install it from https://python.org');
}
