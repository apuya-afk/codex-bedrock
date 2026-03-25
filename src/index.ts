#!/usr/bin/env node
import { Command } from 'commander';
import { setup } from './commands/setup.js';
import { start } from './commands/start.js';
import { stop } from './commands/stop.js';
import { status } from './commands/status.js';

const program = new Command();

program
  .name('codex-bedrock')
  .description('Use Codex CLI with AWS Bedrock + SSO — zero OpenAI account required')
  .version('0.1.0');

program
  .command('setup')
  .description(
    'Interactive one-time setup: installs proxy, configures Codex, adds shell integration',
  )
  .action(setup);

program
  .command('start')
  .description('Start the Bedrock proxy in the foreground')
  .option('-p, --profile <profile>', 'AWS SSO profile to use')
  .option('-r, --region <region>', 'AWS region')
  .action(start);

program.command('stop').description('Stop the running proxy').action(stop);

program.command('status').description('Show proxy status').action(status);

program.parse();
