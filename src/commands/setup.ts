import chalk from 'chalk';
import ora from 'ora';
import { randomBytes } from 'crypto';
import { mkdirSync } from 'fs';
import { CODEX_BEDROCK_DIR, VENV_DIR, PROXY_SRC } from '../utils/paths.js';
import { saveConfig } from '../utils/config.js';
import { checkAwsCli, isSsoSessionValid, listProfiles } from '../utils/aws.js';
import { detectShellRc, injectShellIntegration } from '../utils/shell.js';
import { patchCodexConfig, isCodexInstalled } from '../utils/codex.js';
import { resolvePython } from '../utils/proxy.js';
import { execa } from 'execa';

export async function setup(): Promise<void> {
  const { default: inquirer } = await import('inquirer');

  console.log(chalk.bold('\n🛠  codex-bedrock setup\n'));

  // --- Prerequisites ---
  const spinner = ora('Checking prerequisites').start();

  const [hasAws, hasCodex, python] = await Promise.all([
    checkAwsCli(),
    isCodexInstalled(),
    resolvePython().catch(() => null),
  ]);

  const missing: string[] = [];
  if (!hasAws) missing.push('  • AWS CLI  → https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html');
  if (!hasCodex) missing.push('  • Codex CLI  → brew install codex  or  npm install -g @openai/codex');
  if (!python) missing.push('  • Python 3.11+  → https://python.org');

  if (missing.length) {
    spinner.fail('Missing prerequisites:\n' + missing.join('\n'));
    process.exit(1);
  }
  spinner.succeed('Prerequisites OK');

  // --- AWS profile ---
  const profiles = await listProfiles();
  const { awsProfile } = await inquirer.prompt([
    profiles.length > 0
      ? {
          type: 'list',
          name: 'awsProfile',
          message: 'AWS profile to use:',
          choices: profiles,
        }
      : {
          type: 'input',
          name: 'awsProfile',
          message: 'AWS profile name:',
          default: 'default',
        },
  ]);

  const { awsRegion } = await inquirer.prompt([
    {
      type: 'input',
      name: 'awsRegion',
      message: 'AWS region:',
      default: 'us-east-1',
    },
  ]);

  // Validate SSO session
  const sessionSpinner = ora('Checking AWS SSO session').start();
  const valid = await isSsoSessionValid(awsProfile);
  if (!valid) {
    sessionSpinner.warn('SSO session expired — launching login');
    const { execa } = await import('execa');
    await execa('aws', ['sso', 'login', '--profile', awsProfile], { stdio: 'inherit' });
  } else {
    sessionSpinner.succeed('AWS SSO session valid');
  }

  // --- Port ---
  const { port } = await inquirer.prompt([
    {
      type: 'number',
      name: 'port',
      message: 'Proxy port:',
      default: 51822,
    },
  ]);

  // --- Install proxy ---
  const installSpinner = ora('Installing proxy dependencies').start();
  try {
    mkdirSync(CODEX_BEDROCK_DIR, { recursive: true });
    await execa(python!, ['-m', 'venv', VENV_DIR]);
    await execa(`${VENV_DIR}/bin/pip`, ['install', '-q', '-e', PROXY_SRC]);
    installSpinner.succeed('Proxy installed');
  } catch (err) {
    installSpinner.fail(`Failed to install proxy: ${err}`);
    process.exit(1);
  }

  // --- Build config ---
  const apiKey = randomBytes(16).toString('hex');
  const config = {
    awsProfile,
    awsRegion,
    port,
    apiKey,
    models: {
      flagship: 'us.anthropic.claude-opus-4-6-v1',
      balanced: 'us.anthropic.claude-sonnet-4-6',
      fast: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
    },
  };
  saveConfig(config);

  // --- Patch Codex config ---
  const codexSpinner = ora('Patching ~/.codex/config.toml').start();
  patchCodexConfig(config);
  codexSpinner.succeed('Codex config patched');

  // --- Shell integration ---
  const rcFile = detectShellRc();
  if (rcFile) {
    const shellSpinner = ora(`Adding shell integration to ${rcFile}`).start();
    injectShellIntegration(rcFile, config);
    shellSpinner.succeed(`Shell integration added to ${rcFile}`);
  } else {
    console.log(chalk.yellow('⚠  Could not detect shell RC file — add shell integration manually (see README)'));
  }

  console.log(chalk.green.bold('\n✅ Setup complete!\n'));
  console.log(`Run ${chalk.cyan('source ~/.zshrc && codex')} to get started.`);
  console.log(`\nModel mapping:`);
  console.log(`  ${chalk.cyan('gpt-5.4')} → Claude Opus 4.6   (flagship)`);
  console.log(`  ${chalk.cyan('gpt-5.2')} → Claude Sonnet 4.6 (balanced)`);
  console.log(`  ${chalk.cyan('gpt-5.1')} → Claude Haiku 4.5  (fast)\n`);
}
