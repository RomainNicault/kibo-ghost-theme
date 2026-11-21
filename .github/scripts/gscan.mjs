// Runs gscan on a clean copy of the theme and fails on any Error or Fatal.
// gscan deletes .git and node_modules from the directory it checks, and reads
// templates inside node_modules: never point it at the working tree.
import {cpSync, mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, relative, sep} from 'node:path';
import {spawnSync} from 'node:child_process';

const root = process.cwd();
const skip = new Set(['.git', 'node_modules', 'dist', '.github']);
const copy = join(mkdtempSync(join(tmpdir(), 'kibo-gscan-')), 'theme');
cpSync(root, copy, {
    recursive: true,
    filter: (src) => !relative(root, src).split(sep).some((part) => skip.has(part))
});
const res = spawnSync(join(root, 'node_modules', '.bin', 'gscan'), [copy], {encoding: 'utf8'});
rmSync(join(copy, '..'), {recursive: true, force: true});
const out = (res.stdout || '') + (res.stderr || '');
process.stdout.write(out);
const errors = out.split('\n').filter((line) => /^\s*- (Error|Fatal)/.test(line));
if (errors.length || !/compatible with Ghost|has \d+ warnings?/.test(out)) {
    console.error(`gscan failed: ${errors.length} error line(s)`);
    process.exit(1);
}
