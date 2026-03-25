import chalk from 'chalk';
import { PID_FILE } from '../utils/paths.js';
import { readPid, isRunning } from '../utils/proxy.js';
import { rmSync } from 'fs';

export async function stop(): Promise<void> {
  const pid = readPid();
  if (!pid || !isRunning(pid)) {
    console.log(chalk.yellow('Proxy is not running'));
    return;
  }
  process.kill(pid, 'SIGTERM');
  rmSync(PID_FILE, { force: true });
  console.log(chalk.green(`Proxy stopped (pid ${pid})`));
}
