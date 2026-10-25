import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const here = path.dirname(fileURLToPath(import.meta.url))
const sourcePath = path.join(here, '../src/game/git/sandbox-git.ts')
const source = fs.readFileSync(sourcePath, 'utf8')
const js = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2022,
  },
}).outputText
const moduleUrl = `data:text/javascript,${encodeURIComponent(js)}`
const {
  runGitScript,
  runGitSandboxScript,
  runGitWithCheck,
  checkGitState,
  formatGitChannels,
} = await import(moduleUrl)

function check(condition, message) {
  assert.ok(condition, message)
}

const init = runGitScript(`
git init
write README.md hello
git add README.md
git commit -m "init: hello"
`)
check(init.ok, init.stderr)
check(init.state.branches.main, 'main tip set')

const branch = runGitScript(
  `
git switch -c feature
write docs.md x
git add docs.md
git commit -m "docs"
`,
  init.state,
)
check(branch.ok, branch.stderr)
check(branch.state.head.name === 'feature', 'on feature')

const stash = runGitScript(
  `
write dirty.txt wip
git stash
`,
  init.state,
)
check(stash.ok, stash.stderr)
check(stash.state.stash.length === 1, 'stash saved')
check(!('dirty.txt' in stash.state.workTree), 'clean after stash')

const mergeSeed = runGitScript(`
git init
write README.md base
git add README.md
git commit -m "init"
git switch -c feature
write feature.txt yes
git add feature.txt
git commit -m "feat"
git switch main
git merge feature
`)
check(mergeSeed.ok, mergeSeed.stderr)
check(mergeSeed.state.commits[mergeSeed.state.branches.main].tree['feature.txt'] === 'yes', 'merged')

const checked = runGitWithCheck(
  'git tag v1.0',
  `git init
write README.md base
git add README.md
git commit -m "init"
`,
  { tags: ['v1.0'] },
)
check(checked.passed, checked.feedback)

const fail = checkGitState(init.state, { branch: 'nope' })
check(!fail.passed, 'expect fail on wrong branch')

const statusOnly = runGitSandboxScript(`
git status
git add file.txt
git diff
git diff --staged
`)
check(statusOnly.ok, statusOnly.stderr || statusOnly.stdout)
check(!formatGitChannels(statusOnly).includes('fatal: not a git repository'), 'status snippet stays inside a repo')
check(statusOnly.stdout.includes('diff --git'), 'staged diff after add')

const initSnippet = runGitSandboxScript(`
git init
git add README.md
git commit -m "init: учебный репозиторий"
`)
check(initSnippet.ok, initSnippet.stderr)
check(initSnippet.state.commits[initSnippet.state.branches.main].tree['README.md'], 'README created for add')
check(!('extra.txt' in initSnippet.state.workTree), 'git init does not use the demo repo')

const pull = runGitSandboxScript(`
git fetch origin
git pull origin
`)
check(pull.ok, pull.stderr)
check(pull.state.commits[pull.state.branches.main].tree['remote-only.txt'] === 'from remote', 'pull fast-forwards demo remote')

const stashBlock = runGitSandboxScript(`
git stash
git stash list
git stash pop
git stash apply
git stash drop
git stash clear
`)
check(stashBlock.ok, stashBlock.stderr)

console.log('check-git-sandbox: ok')
