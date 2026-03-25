import chalk from 'chalk';
import { execa } from 'execa';
import { writeFileSync } from 'fs';
import { VENV_DIR, PID_FILE, LOG_FILE } from '../utils/paths.js';
import { loadConfig } from '../utils/config.js';
import { buildEnv } from '../utils/proxy.js';
import { isSsoSessionValid, ssoLogin } from '../utils/aws.js';

interface StartOptions {
  profile?: string;
  region?: string;
}

export async function start(options: StartOptions): Promise<void> {
  const config = loadConfig();
  if (options.profile) config.awsProfile = options.profile;
  if (options.region) config.awsRegion = options.region;

  // Validate / refresh SSO session
  const valid = await isSsoSessionValid(config.awsProfile);
  if (!valid) {
    console.log(chalk.yellow('SSO session expired — logging in...'));
    await ssoLogin(config.awsProfile);
  }

  console.log(chalk.cyan(`Starting proxy on http://127.0.0.1:${config.port}`));

  const uvicorn = `${VENV_DIR}/bin/uvicorn`;
  const proc = execa(
    uvicorn,
    ['codex_bedrock.app:app', '--host', '127.0.0.1', '--port', String(config.port), '--ws', 'websockets'],
    { env: buildEnv(config), stdio: 'inherit' },
  );

  if (proc.pid) writeFileSync(PID_FILE, String(proc.pid));

  try {
    await proc;
  } catch (err: unknown) {
    if ((err as NodeJS.ErrnoException).signal !== 'SIGTERM') {
      console.error(chalk.red('Proxy exited with error:'), err);
      process.exit(1);
    }
  }
}
