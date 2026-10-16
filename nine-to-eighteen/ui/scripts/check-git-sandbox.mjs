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
  runGitWithCheck,
  checkGitState,
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

console.log('check-git-sandbox: ok')
