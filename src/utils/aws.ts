import { execa } from 'execa';

export async function checkAwsCli(): Promise<boolean> {
  try {
    await execa('aws', ['--version']);
    return true;
  } catch {
    return false;
  }
}

export async function isSsoSessionValid(profile: string): Promise<boolean> {
  try {
    await execa('aws', ['sts', 'get-caller-identity', '--profile', profile]);
    return true;
  } catch {
    return false;
  }
}

export async function ssoLogin(profile: string): Promise<void> {
  await execa('aws', ['sso', 'login', '--profile', profile], { stdio: 'inherit' });
}

export async function listProfiles(): Promise<string[]> {
  try {
    const { stdout } = await execa('aws', ['configure', 'list-profiles']);
    return stdout.trim().split('\n').filter(Boolean);
  } catch {
    return [];
  }
}
