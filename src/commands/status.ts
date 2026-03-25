import chalk from 'chalk';
import { loadConfig } from '../utils/config.js';
import { proxyStatus } from '../utils/proxy.js';

export async function status(): Promise<void> {
  const config = loadConfig();
  const { running, pid } = proxyStatus();

  if (running && pid) {
    console.log(chalk.green(`● Proxy running`) + chalk.dim(` (pid ${pid}, port ${config.port})`));
  } else {
    console.log(chalk.red('○ Proxy not running'));
  }

  console.log(chalk.dim('\nModel mapping:'));
  console.log(`  gpt-5.4 → ${config.models.flagship}`);
  console.log(`  gpt-5.2 → ${config.models.balanced}`);
  console.log(`  gpt-5.1 → ${config.models.fast}`);
}
