/** In-browser Git simulator (no real .git on disk). */

export type GitCommit = {
  hash: string
  message: string
  parents: string[]
  /** path → content */
  tree: Record<string, string>
  author: string
  time: number
}

export type GitTag = {
  name: string
  hash: string
  annotated: boolean
  message?: string
}

export type GitRemote = {
  url: string
  /** branch → commit hash */
  branches: Record<string, string>
  /** commit store shared conceptually with local for simplicity */
}

export type GitStashEntry = {
  message: string
  workTree: Record<string, string>
  index: Record<string, string>
  headHash: string | null
}

export type GitState = {
  initialized: boolean
  workTree: Record<string, string>
  index: Record<string, string>
  commits: Record<string, GitCommit>
  branches: Record<string, string>
  head: { type: 'branch'; name: string } | { type: 'detached'; hash: string }
  remotes: Record<string, GitRemote>
  stash: GitStashEntry[]
  tags: GitTag[]
  config: Record<string, string>
  /** bisect session */
  bisect: {
    active: boolean
    bad: string | null
    good: string | null
    current: string | null
  } | null
  clock: number
}

export type GitRunResult = {
  stdout: string
  stderr: string
  ok: boolean
  state: GitState
}

export type GitCheckExpect = {
  branch?: string
  /** files present in HEAD commit */
  headFiles?: Record<string, string>
  /** exact index paths (content optional via headFiles-like) */
  indexPaths?: string[]
  indexMissing?: string[]
  workTreePaths?: string[]
  workTreeMissing?: string[]
  stashCount?: number
  remotes?: Record<string, string>
  tags?: string[]
  /** branch names that should appear in --merged of current HEAD */
  merged?: string[]
  /** HEAD commit message substring */
  headMessageIncludes?: string
  /** file must NOT be in HEAD tree */
  headMissingFiles?: string[]
  /** bisect result hash prefix or exact */
  bisectFound?: string
  /** message of commit found by bisect */
  bisectMessageIncludes?: string
}

function cloneRecord<T>(obj: Record<string, T>): Record<string, T> {
  return { ...obj }
}

function simpleHash(input: string): string {
  let h = 2166136261
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return (h >>> 0).toString(16).padStart(8, '0')
}

export function createEmptyState(): GitState {
  return {
    initialized: false,
    workTree: {},
    index: {},
    commits: {},
    branches: {},
    head: { type: 'branch', name: 'main' },
    remotes: {},
    stash: [],
    tags: [],
    config: {
      'user.name': '9to18',
      'user.email': 'git@9to18.local',
    },
    bisect: null,
    clock: 1,
  }
}

export function cloneState(state: GitState): GitState {
  return {
    initialized: state.initialized,
    workTree: cloneRecord(state.workTree),
    index: cloneRecord(state.index),
    commits: Object.fromEntries(
      Object.entries(state.commits).map(([k, c]) => [
        k,
        { ...c, parents: [...c.parents], tree: cloneRecord(c.tree) },
      ]),
    ),
    branches: cloneRecord(state.branches),
    head:
      state.head.type === 'branch'
        ? { type: 'branch', name: state.head.name }
        : { type: 'detached', hash: state.head.hash },
    remotes: Object.fromEntries(
      Object.entries(state.remotes).map(([name, remote]) => [
        name,
        { url: remote.url, branches: cloneRecord(remote.branches) },
      ]),
    ),
    stash: state.stash.map((entry) => ({
      ...entry,
      workTree: cloneRecord(entry.workTree),
      index: cloneRecord(entry.index),
    })),
    tags: state.tags.map((tag) => ({ ...tag })),
    config: cloneRecord(state.config),
    bisect: state.bisect
      ? { ...state.bisect }
      : null,
    clock: state.clock,
  }
}

function headHash(state: GitState): string | null {
  if (state.head.type === 'detached') {
    return state.head.hash || null
  }
  const hash = state.branches[state.head.name]
  return hash || null
}

function resolveRef(state: GitState, ref: string): string | null {
  if (!ref || ref === 'HEAD') {
    return headHash(state)
  }
  if (state.branches[ref]) {
    return state.branches[ref]
  }
  if (state.commits[ref]) {
    return ref
  }
  const short = Object.keys(state.commits).find((hash) => hash.startsWith(ref))
  if (short) return short
  const tilde = /^(HEAD|[\w./-]+)~(\d+)$/.exec(ref)
  if (tilde) {
    let cur = resolveRef(state, tilde[1])
    const steps = Number(tilde[2])
    for (let i = 0; i < steps; i += 1) {
      if (!cur) return null
      const commit = state.commits[cur]
      if (!commit?.parents[0]) return null
      cur = commit.parents[0]
    }
    return cur
  }
  return null
}

function headCommit(state: GitState): GitCommit | null {
  const hash = headHash(state)
  return hash ? state.commits[hash] || null : null
}

function requireInit(state: GitState): void {
  if (!state.initialized) {
    throw new Error('not a git repository (run git init)')
  }
}

function parseArgs(line: string): string[] {
  const parts: string[] = []
  let cur = ''
  let quote: '"' | "'" | null = null
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]
    if (quote) {
      if (ch === quote) {
        quote = null
      } else {
        cur += ch
      }
      continue
    }
    if (ch === '"' || ch === "'") {
      quote = ch
      continue
    }
    if (/\s/.test(ch)) {
      if (cur) {
        parts.push(cur)
        cur = ''
      }
      continue
    }
    cur += ch
  }
  if (cur) parts.push(cur)
  return parts
}

function treesEqual(a: Record<string, string>, b: Record<string, string>): boolean {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)])
  for (const key of keys) {
    if ((a[key] ?? null) !== (b[key] ?? null)) return false
  }
  return true
}

function makeCommit(
  state: GitState,
  message: string,
  tree: Record<string, string>,
  parents: string[],
): GitCommit {
  state.clock += 1
  const payload = JSON.stringify({ message, tree, parents, t: state.clock })
  const hash = simpleHash(payload)
  const commit: GitCommit = {
    hash,
    message,
    parents,
    tree: cloneRecord(tree),
    author: state.config['user.name'] || '9to18',
    time: state.clock,
  }
  state.commits[hash] = commit
  return commit
}

function setHeadCommit(state: GitState, hash: string): void {
  if (state.head.type === 'branch') {
    state.branches[state.head.name] = hash
  } else {
    state.head = { type: 'detached', hash }
  }
}

function checkoutTree(state: GitState, tree: Record<string, string>): void {
  state.workTree = cloneRecord(tree)
  state.index = cloneRecord(tree)
}

function isAncestor(
  state: GitState,
  ancestor: string,
  descendant: string,
): boolean {
  if (ancestor === descendant) return true
  const seen = new Set<string>()
  const stack = [descendant]
  while (stack.length) {
    const cur = stack.pop()!
    if (seen.has(cur)) continue
    seen.add(cur)
    if (cur === ancestor) return true
    const commit = state.commits[cur]
    if (!commit) continue
    for (const parent of commit.parents) {
      stack.push(parent)
    }
  }
  return false
}

function findMergeBase(state: GitState, a: string, b: string): string | null {
  const ancestorsA = new Set<string>()
  const stack = [a]
  while (stack.length) {
    const cur = stack.pop()!
    if (ancestorsA.has(cur)) continue
    ancestorsA.add(cur)
    const commit = state.commits[cur]
    if (commit) stack.push(...commit.parents)
  }
  const queueB = [b]
  const seen = new Set<string>()
  while (queueB.length) {
    const cur = queueB.shift()!
    if (seen.has(cur)) continue
    seen.add(cur)
    if (ancestorsA.has(cur)) return cur
    const commit = state.commits[cur]
    if (commit) queueB.push(...commit.parents)
  }
  return null
}

function mergeTrees(
  base: Record<string, string>,
  ours: Record<string, string>,
  theirs: Record<string, string>,
): Record<string, string> {
  const paths = new Set([
    ...Object.keys(base),
    ...Object.keys(ours),
    ...Object.keys(theirs),
  ])
  const out: Record<string, string> = {}
  for (const path of paths) {
    const b = base[path]
    const o = ours[path]
    const t = theirs[path]
    if (o === t) {
      if (o !== undefined) out[path] = o
      continue
    }
    if (o === b) {
      if (t !== undefined) out[path] = t
      continue
    }
    if (t === b) {
      if (o !== undefined) out[path] = o
      continue
    }
    // conflict: prefer theirs with marker content for visibility
    out[path] = t ?? o ?? ''
  }
  return out
}

function statusText(state: GitState): string {
  if (!state.initialized) return 'fatal: not a git repository'
  const branch =
    state.head.type === 'branch'
      ? `On branch ${state.head.name}`
      : `HEAD detached at ${state.head.hash.slice(0, 7)}`
  const head = headCommit(state)
  const headTree = head?.tree || {}
  const staged: string[] = []
  const unstaged: string[] = []
  const untracked: string[] = []
  const paths = new Set([
    ...Object.keys(state.workTree),
    ...Object.keys(state.index),
    ...Object.keys(headTree),
  ])
  for (const path of [...paths].sort()) {
    const inHead = headTree[path]
    const inIndex = state.index[path]
    const inWork = state.workTree[path]
    if (inIndex !== undefined && inIndex !== inHead) {
      staged.push(inHead === undefined ? `new file:   ${path}` : `modified:   ${path}`)
    }
    if (inIndex !== undefined && inHead !== undefined && !(path in state.index) === false) {
      /* keep */
    }
    if (inIndex === undefined && inHead !== undefined) {
      staged.push(`deleted:    ${path}`)
    }
    if (inWork !== undefined && inWork !== inIndex) {
      if (inIndex === undefined && inHead === undefined) {
        untracked.push(path)
      } else {
        unstaged.push(`modified:   ${path}`)
      }
    }
    if (inWork === undefined && inIndex !== undefined) {
      unstaged.push(`deleted:    ${path}`)
    }
  }
  const lines = [branch, '']
  if (staged.length) {
    lines.push('Changes to be committed:')
    staged.forEach((line) => lines.push(`\t${line}`))
    lines.push('')
  }
  if (unstaged.length) {
    lines.push('Changes not staged for commit:')
    unstaged.forEach((line) => lines.push(`\t${line}`))
    lines.push('')
  }
  if (untracked.length) {
    lines.push('Untracked files:')
    untracked.forEach((line) => lines.push(`\t${line}`))
    lines.push('')
  }
  if (!staged.length && !unstaged.length && !untracked.length) {
    lines.push('nothing to commit, working tree clean')
  }
  return lines.join('\n')
}

function runGitCommand(state: GitState, args: string[]): string {
  const cmd = args[0]
  if (!cmd) return ''

  if (cmd === 'init') {
    state.initialized = true
    if (!state.branches.main && !Object.keys(state.branches).length) {
      state.branches.main = ''
      state.head = { type: 'branch', name: 'main' }
    }
    return 'Initialized empty Git repository'
  }

  if (cmd === 'clone') {
    // git clone <name> — load remote snapshot named origin-like into new repo
    const remoteName = args[1] || 'origin'
    const remote = state.remotes[remoteName]
    if (!remote) {
      throw new Error(`remote ${remoteName} not found (seed a remote first)`)
    }
    const branch = Object.keys(remote.branches)[0]
    if (!branch) throw new Error('remote has no branches')
    const hash = remote.branches[branch]
    const commit = state.commits[hash]
    if (!commit) throw new Error('remote tip missing')
    state.initialized = true
    state.branches = { [branch]: hash }
    state.head = { type: 'branch', name: branch }
    checkoutTree(state, commit.tree)
    state.remotes.origin = {
      url: remote.url,
      branches: cloneRecord(remote.branches),
    }
    return `Cloning into '.'...\nChecking out files: 100%`
  }

  requireInit(state)

  if (cmd === 'status') {
    return statusText(state)
  }

  if (cmd === 'add') {
    const paths = args.slice(1)
    if (!paths.length) throw new Error('nothing specified, nothing added')
    for (const path of paths) {
      if (path === '.' || path === '-A' || path === '--all') {
        for (const [p, content] of Object.entries(state.workTree)) {
          state.index[p] = content
        }
        for (const p of Object.keys(state.index)) {
          if (!(p in state.workTree)) {
            delete state.index[p]
          }
        }
        continue
      }
      if (!(path in state.workTree)) {
        if (path in state.index) {
          delete state.index[path]
        } else {
          throw new Error(`pathspec '${path}' did not match any files`)
        }
      } else {
        state.index[path] = state.workTree[path]
      }
    }
    return ''
  }

  if (cmd === 'commit') {
    let message = ''
    for (let i = 1; i < args.length; i += 1) {
      if (args[i] === '-m' && args[i + 1]) {
        message = args[i + 1]
        break
      }
    }
    if (!message) throw new Error('aborting commit due to empty message (use -m)')
    const parent = headHash(state)
    const parentCommit = parent ? state.commits[parent] : null
    const parentTree = parentCommit?.tree || {}
    if (treesEqual(state.index, parentTree) && parent) {
      throw new Error('nothing to commit, working tree clean')
    }
    const commit = makeCommit(
      state,
      message,
      cloneRecord(state.index),
      parent ? [parent] : [],
    )
    setHeadCommit(state, commit.hash)
    return `[${state.head.type === 'branch' ? state.head.name : 'detached'} ${commit.hash.slice(0, 7)}] ${message}`
  }

  if (cmd === 'log') {
    const oneline = args.includes('--oneline')
    let cur = headHash(state)
    const lines: string[] = []
    const seen = new Set<string>()
    while (cur && !seen.has(cur)) {
      seen.add(cur)
      const commit = state.commits[cur]
      if (!commit) break
      lines.push(
        oneline
          ? `${commit.hash.slice(0, 7)} ${commit.message}`
          : `commit ${commit.hash}\nAuthor: ${commit.author}\n\n    ${commit.message}\n`,
      )
      cur = commit.parents[0] || null
    }
    return lines.join(oneline ? '\n' : '\n') || ''
  }

  if (cmd === 'show') {
    const ref = args[1] || headHash(state) || ''
    const commit = state.commits[ref] || state.commits[headHash(state) || '']
    if (!commit) throw new Error('unknown revision')
    const files = Object.keys(commit.tree).sort().join('\n')
    return `commit ${commit.hash}\n\n    ${commit.message}\n\nFiles:\n${files}`
  }

  if (cmd === 'branch') {
    if (args.includes('--merged')) {
      const tip = headHash(state)
      if (!tip) return ''
      return Object.keys(state.branches)
        .filter((name) => {
          const h = state.branches[name]
          return h && isAncestor(state, h, tip)
        })
        .map((name) => {
          const cur =
            state.head.type === 'branch' && state.head.name === name ? '* ' : '  '
          return `${cur}${name}`
        })
        .join('\n')
    }
    if (args[1] === '-m') {
      const a = args[2]
      const b = args[3]
      if (!a) throw new Error('branch name required')
      if (b) {
        if (!state.branches[a]) throw new Error(`branch '${a}' not found`)
        state.branches[b] = state.branches[a]
        delete state.branches[a]
        if (state.head.type === 'branch' && state.head.name === a) {
          state.head = { type: 'branch', name: b }
        }
      } else {
        if (state.head.type !== 'branch') {
          throw new Error('not on a branch')
        }
        const old = state.head.name
        state.branches[a] = state.branches[old]
        delete state.branches[old]
        state.head = { type: 'branch', name: a }
      }
      return ''
    }
    if (args[1] && !args[1].startsWith('-')) {
      const name = args[1]
      const tip = headHash(state)
      if (!tip) throw new Error('no commits yet')
      if (state.branches[name]) throw new Error(`branch '${name}' already exists`)
      state.branches[name] = tip
      return ''
    }
    return Object.keys(state.branches)
      .sort()
      .map((name) => {
        const cur =
          state.head.type === 'branch' && state.head.name === name ? '* ' : '  '
        return `${cur}${name}`
      })
      .join('\n')
  }

  if (cmd === 'switch' || cmd === 'checkout') {
    const create = args.includes('-c') || args.includes('-b')
    const name = args.filter((a) => !a.startsWith('-')).slice(1)[0] || args[args.length - 1]
    if (!name || name === 'switch' || name === 'checkout') {
      throw new Error('branch name required')
    }
    if (create) {
      const tip = headHash(state)
      if (!tip) throw new Error('no commits yet')
      if (state.branches[name]) throw new Error(`branch '${name}' already exists`)
      state.branches[name] = tip
      state.head = { type: 'branch', name }
      return `Switched to a new branch '${name}'`
    }
    if (!state.branches[name]) throw new Error(`pathspec '${name}' did not match`)
    const hash = state.branches[name]
    state.head = { type: 'branch', name }
    if (hash && state.commits[hash]) {
      checkoutTree(state, state.commits[hash].tree)
    }
    return `Switched to branch '${name}'`
  }

  if (cmd === 'rm') {
    const cached = args.includes('--cached')
    const paths = args.filter((a) => !a.startsWith('-') && a !== 'rm')
    if (!paths.length) throw new Error('no paths')
    for (const path of paths) {
      if (cached) {
        if (!(path in state.index)) {
          throw new Error(`pathspec '${path}' did not match`)
        }
        delete state.index[path]
      } else {
        delete state.index[path]
        delete state.workTree[path]
      }
    }
    return `rm '${paths.join("', '")}'`
  }

  if (cmd === 'remote') {
    if (args[1] === '-v' || (args.length === 1)) {
      return Object.entries(state.remotes)
        .map(([name, remote]) => `${name}\t${remote.url} (fetch)\n${name}\t${remote.url} (push)`)
        .join('\n')
    }
    if (args[1] === 'add') {
      const name = args[2]
      const url = args[3]
      if (!name || !url) throw new Error('usage: git remote add <name> <url>')
      state.remotes[name] = { url, branches: {} }
      return ''
    }
    if (args[1] === 'set-url') {
      const name = args[2]
      const url = args[3]
      if (!name || !url) throw new Error('usage: git remote set-url <name> <url>')
      if (!state.remotes[name]) throw new Error(`No such remote: ${name}`)
      state.remotes[name].url = url
      return ''
    }
    throw new Error(`unsupported remote subcommand`)
  }

  if (cmd === 'fetch') {
    const name = args[1] || 'origin'
    const remote = state.remotes[name]
    if (!remote) throw new Error(`No such remote: ${name}`)
    // Remote tip already in remotes[name].branches; tracking refs stored as remotes/name/branch conceptually via remote.branches
    return `From ${remote.url}\n * [new branch]      main -> ${name}/main`
  }

  if (cmd === 'pull') {
    const name = args[1] || 'origin'
    const remote = state.remotes[name]
    if (!remote) throw new Error(`No such remote: ${name}`)
    const branch =
      state.head.type === 'branch' ? state.head.name : 'main'
    const remoteTip = remote.branches[branch] || remote.branches.main
    if (!remoteTip) throw new Error('remote has no tip')
    const localTip = headHash(state)
    if (!localTip) {
      setHeadCommit(state, remoteTip)
      checkoutTree(state, state.commits[remoteTip].tree)
      return `Updating ${remoteTip.slice(0, 7)}\nFast-forward`
    }
    if (localTip === remoteTip) return 'Already up to date.'
    if (isAncestor(state, localTip, remoteTip)) {
      setHeadCommit(state, remoteTip)
      checkoutTree(state, state.commits[remoteTip].tree)
      return `Updating ${localTip.slice(0, 7)}..${remoteTip.slice(0, 7)}\nFast-forward`
    }
    const base = findMergeBase(state, localTip, remoteTip) || localTip
    const merged = mergeTrees(
      state.commits[base]?.tree || {},
      state.commits[localTip].tree,
      state.commits[remoteTip].tree,
    )
    const commit = makeCommit(state, `Merge remote-tracking branch '${name}/${branch}'`, merged, [
      localTip,
      remoteTip,
    ])
    setHeadCommit(state, commit.hash)
    checkoutTree(state, merged)
    return 'Merge made by the recursive strategy.'
  }

  if (cmd === 'stash') {
    const sub = args[1] || 'push'
    if (sub === 'list') {
      return state.stash
        .map((entry, i) => `stash@{${i}}: ${entry.message}`)
        .join('\n')
    }
    if (sub === 'drop') {
      if (!state.stash.length) throw new Error('No stash entries found.')
      state.stash.shift()
      return 'Dropped refs/stash@{0}'
    }
    if (sub === 'clear') {
      state.stash = []
      return ''
    }
    if (sub === 'pop' || sub === 'apply') {
      if (!state.stash.length) throw new Error('No stash entries found.')
      const entry = state.stash[0]
      state.workTree = { ...state.workTree, ...entry.workTree }
      state.index = { ...state.index, ...entry.index }
      if (sub === 'pop') state.stash.shift()
      return 'On branch ...\nChanges not staged for commit:\n  (use git add ...)\nDropped refs/stash@{0} (pop)'.replace(
        '(pop)',
        sub === 'pop' ? '' : '(kept)',
      )
    }
    // push / save
    const head = headCommit(state)
    const dirty =
      !treesEqual(state.workTree, state.index) ||
      !treesEqual(state.index, head?.tree || {})
    if (!dirty && treesEqual(state.workTree, head?.tree || {})) {
      throw new Error('No local changes to save')
    }
    state.stash.unshift({
      message: args[2] || 'WIP on branch',
      workTree: cloneRecord(state.workTree),
      index: cloneRecord(state.index),
      headHash: headHash(state),
    })
    if (head) checkoutTree(state, head.tree)
    else {
      state.workTree = {}
      state.index = {}
    }
    return 'Saved working directory and index state'
  }

  if (cmd === 'merge') {
    const name = args[1]
    if (!name) throw new Error('branch required')
    const theirHash = state.branches[name]
    if (!theirHash) throw new Error(`merge: ${name} - not something we can merge`)
    const ourHash = headHash(state)
    if (!ourHash) throw new Error('no commits')
    if (ourHash === theirHash) return 'Already up to date.'
    if (isAncestor(state, ourHash, theirHash)) {
      setHeadCommit(state, theirHash)
      checkoutTree(state, state.commits[theirHash].tree)
      return `Updating ${ourHash.slice(0, 7)}..${theirHash.slice(0, 7)}\nFast-forward`
    }
    const base = findMergeBase(state, ourHash, theirHash) || ourHash
    const merged = mergeTrees(
      state.commits[base]?.tree || {},
      state.commits[ourHash].tree,
      state.commits[theirHash].tree,
    )
    const commit = makeCommit(state, `Merge branch '${name}'`, merged, [
      ourHash,
      theirHash,
    ])
    setHeadCommit(state, commit.hash)
    checkoutTree(state, merged)
    return `Merge made by the 'ort' strategy.`
  }

  if (cmd === 'rebase') {
    const onto = args[1]
    if (!onto) throw new Error('branch required')
    const ontoHash = state.branches[onto]
    if (!ontoHash) throw new Error(`invalid upstream ${onto}`)
    const ourHash = headHash(state)
    if (!ourHash) throw new Error('no commits')
    if (isAncestor(state, ourHash, ontoHash)) {
      setHeadCommit(state, ontoHash)
      checkoutTree(state, state.commits[ontoHash].tree)
      return 'Successfully rebased and updated'
    }
    // Linear replay: take tip message onto new base if fast divergence — simplified: reset to onto + replay one tip commit
    const tip = state.commits[ourHash]
    const commit = makeCommit(state, tip.message, tip.tree, [ontoHash])
    setHeadCommit(state, commit.hash)
    checkoutTree(state, tip.tree)
    return 'Successfully rebased and updated'
  }

  if (cmd === 'reset') {
    const hard = args.includes('--hard')
    const soft = args.includes('--soft')
    const target = args.find((a) => a === 'HEAD~' || a === 'HEAD~1') || 'HEAD~'
    if (target.startsWith('HEAD~')) {
      const cur = headHash(state)
      if (!cur) throw new Error('no commits')
      const commit = state.commits[cur]
      const parent = commit.parents[0]
      if (!parent) throw new Error('no parent')
      setHeadCommit(state, parent)
      if (hard) {
        checkoutTree(state, state.commits[parent].tree)
      } else if (soft) {
        // keep index and worktree
      } else {
        // mixed: index = parent, keep worktree as was (files from undone commit become unstaged)
        state.index = cloneRecord(state.commits[parent].tree)
        // worktree keeps tip tree files so they appear as unstaged
        state.workTree = cloneRecord(commit.tree)
      }
      return ''
    }
    throw new Error('unsupported reset target')
  }

  if (cmd === 'tag') {
    if (args.length === 1) {
      return state.tags.map((t) => t.name).sort().join('\n')
    }
    let annotated = false
    let message = ''
    let name = ''
    for (let i = 1; i < args.length; i += 1) {
      if (args[i] === '-a') {
        annotated = true
        continue
      }
      if (args[i] === '-m') {
        message = args[i + 1] || ''
        i += 1
        continue
      }
      if (!args[i].startsWith('-')) name = args[i]
    }
    const hash = headHash(state)
    if (!hash) throw new Error('no commits')
    if (!name) throw new Error('tag name required')
    if (state.tags.some((t) => t.name === name)) {
      throw new Error(`tag '${name}' already exists`)
    }
    state.tags.push({ name, hash, annotated, message })
    return ''
  }

  if (cmd === 'config') {
    if (args[1] === '--get' || (args.length === 2 && !args[1].includes('='))) {
      const key = args[1] === '--get' ? args[2] : args[1]
      return state.config[key] || ''
    }
    const key = args[1]
    const value = args[2]
    if (!key || value === undefined) throw new Error('usage: git config <key> <value>')
    state.config[key] = value
    return ''
  }

  if (cmd === 'bisect') {
    const sub = args[1]
    if (sub === 'start') {
      state.bisect = { active: true, bad: null, good: null, current: headHash(state) }
      return 'status: waiting for both good and bad commits'
    }
    if (!state.bisect?.active) throw new Error('Need to start bisect first')
    if (sub === 'bad') {
      const hash = args[2] ? resolveRef(state, args[2]) : headHash(state)
      if (!hash) throw new Error('no hash')
      state.bisect.bad = hash
      return tryBisect(state)
    }
    if (sub === 'good') {
      const hash = args[2] ? resolveRef(state, args[2]) : null
      if (!hash) throw new Error('good commit required')
      state.bisect.good = hash
      return tryBisect(state)
    }
    if (sub === 'reset') {
      state.bisect = null
      return ''
    }
    throw new Error(`unknown bisect command ${sub}`)
  }

  throw new Error(`unsupported command: git ${cmd}`)
}

function tryBisect(state: GitState): string {
  const session = state.bisect!
  if (!session.good || !session.bad) {
    return 'status: waiting for both good and bad commits'
  }
  // Walk bad → … → stop before good; last pushed is first bad (child of good).
  let cur: string | null = session.bad
  const path: string[] = []
  while (cur && cur !== session.good) {
    path.push(cur)
    const node: GitCommit | undefined = state.commits[cur]
    if (!node || !node.parents.length) break
    const parentHash: string = node.parents[0]
    if (parentHash === session.good) break
    cur = parentHash
  }
  const found = path[path.length - 1] || session.bad
  session.current = found
  const foundCommit: GitCommit | undefined = state.commits[found]
  return `${found.slice(0, 7)} is the first bad commit\n${foundCommit?.message || ''}`
}

/** Simulator helpers: write <path> <content...>, rmfile <path>, seed-remote ... */
function runHelper(state: GitState, args: string[]): string {
  const cmd = args[0]
  if (cmd === 'write') {
    const path = args[1]
    const content = args.slice(2).join(' ')
    if (!path) throw new Error('write <path> <content>')
    state.workTree[path] = content
    return `wrote ${path}`
  }
  if (cmd === 'rmfile') {
    const path = args[1]
    if (!path) throw new Error('rmfile <path>')
    delete state.workTree[path]
    return `removed ${path}`
  }
  if (cmd === 'seed-remote') {
    // seed-remote <name> <url> <branch> <commitHash>
    // Or build: seed-remote origin https://example/repo.git main
    // uses current HEAD as remote tip
    const name = args[1] || 'origin'
    const url = args[2] || `https://example.com/${name}.git`
    const branch = args[3] || 'main'
    const hash = args[4] || headHash(state)
    if (!hash) throw new Error('no commit to seed remote')
    state.remotes[name] = {
      url,
      branches: { [branch]: hash },
    }
    return `seeded remote ${name}`
  }
  if (cmd === 'seed-remote-ahead') {
    // Create a new commit only on remote (local stays behind)
    const name = args[1] || 'origin'
    const remote = state.remotes[name]
    if (!remote) throw new Error('remote missing')
    const branch = Object.keys(remote.branches)[0] || 'main'
    const tip = remote.branches[branch]
    const base = state.commits[tip]
    if (!base) throw new Error('remote tip missing')
    const tree = { ...base.tree, 'remote-only.txt': 'from remote' }
    const commit = makeCommit(state, 'remote: ahead commit', tree, [tip])
    remote.branches[branch] = commit.hash
    return `remote ${name}/${branch} → ${commit.hash.slice(0, 7)}`
  }
  throw new Error(`unknown helper ${cmd}`)
}

/**
 * Run a multi-line script. Lines starting with # are comments.
 * Supports `git …`, `write …`, `rmfile …`, `seed-remote …`.
 */
export function runGitScript(
  script: string,
  initial?: GitState,
): GitRunResult {
  const state = cloneState(initial || createEmptyState())
  const out: string[] = []
  const err: string[] = []
  let ok = true
  const lines = script.split(/\r?\n/)
  for (const raw of lines) {
    const line = raw.trim()
    if (!line || line.startsWith('#')) continue
    try {
      const args = parseArgs(line)
      if (args[0] === 'git') {
        const text = runGitCommand(state, args.slice(1))
        if (text) out.push(text)
      } else {
        const text = runHelper(state, args)
        if (text) out.push(text)
      }
    } catch (error) {
      ok = false
      err.push(error instanceof Error ? error.message : String(error))
      break
    }
  }
  return {
    stdout: out.join('\n'),
    stderr: err.join('\n'),
    ok,
    state,
  }
}

export function checkGitState(
  state: GitState,
  expect: GitCheckExpect,
): { passed: boolean; feedback: string } {
  if (expect.branch !== undefined) {
    if (state.head.type !== 'branch' || state.head.name !== expect.branch) {
      return {
        passed: false,
        feedback: `ожидали ветку ${expect.branch}, сейчас ${
          state.head.type === 'branch' ? state.head.name : 'detached'
        }`,
      }
    }
  }
  if (expect.headFiles) {
    const head = headCommit(state)
    if (!head) {
      return { passed: false, feedback: 'нет HEAD commit' }
    }
    for (const [path, content] of Object.entries(expect.headFiles)) {
      if (head.tree[path] !== content) {
        return {
          passed: false,
          feedback: `HEAD файл ${path}: ожидали ${JSON.stringify(content)}, получили ${JSON.stringify(head.tree[path])}`,
        }
      }
    }
  }
  if (expect.headMissingFiles) {
    const head = headCommit(state)
    for (const path of expect.headMissingFiles) {
      if (head?.tree[path] !== undefined) {
        return { passed: false, feedback: `файл ${path} не должен быть в HEAD` }
      }
    }
  }
  if (expect.headMessageIncludes) {
    const head = headCommit(state)
    if (!head?.message.includes(expect.headMessageIncludes)) {
      return {
        passed: false,
        feedback: `сообщение HEAD должно содержать «${expect.headMessageIncludes}»`,
      }
    }
  }
  if (expect.indexPaths) {
    for (const path of expect.indexPaths) {
      if (!(path in state.index)) {
        return { passed: false, feedback: `${path} должен быть в index` }
      }
    }
  }
  if (expect.indexMissing) {
    for (const path of expect.indexMissing) {
      if (path in state.index) {
        return { passed: false, feedback: `${path} не должен быть в index` }
      }
    }
  }
  if (expect.workTreePaths) {
    for (const path of expect.workTreePaths) {
      if (!(path in state.workTree)) {
        return { passed: false, feedback: `${path} должен быть в working tree` }
      }
    }
  }
  if (expect.workTreeMissing) {
    for (const path of expect.workTreeMissing) {
      if (path in state.workTree) {
        return { passed: false, feedback: `${path} не должен быть в working tree` }
      }
    }
  }
  if (expect.stashCount !== undefined) {
    if (state.stash.length !== expect.stashCount) {
      return {
        passed: false,
        feedback: `stash: ожидали ${expect.stashCount}, получили ${state.stash.length}`,
      }
    }
  }
  if (expect.remotes) {
    for (const [name, url] of Object.entries(expect.remotes)) {
      if (state.remotes[name]?.url !== url) {
        return {
          passed: false,
          feedback: `remote ${name}: ожидали ${url}, получили ${state.remotes[name]?.url}`,
        }
      }
    }
  }
  if (expect.tags) {
    const have = new Set(state.tags.map((t) => t.name))
    for (const name of expect.tags) {
      if (!have.has(name)) {
        return { passed: false, feedback: `нет тега ${name}` }
      }
    }
  }
  if (expect.merged) {
    const tip = headHash(state)
    if (!tip) return { passed: false, feedback: 'нет HEAD' }
    for (const name of expect.merged) {
      const h = state.branches[name]
      if (!h || !isAncestor(state, h, tip)) {
        return { passed: false, feedback: `ветка ${name} не смержена в HEAD` }
      }
    }
  }
  if (expect.bisectFound) {
    const found = state.bisect?.current
    if (!found || !found.startsWith(expect.bisectFound)) {
      return {
        passed: false,
        feedback: `bisect: ожидали ${expect.bisectFound}…, получили ${found}`,
      }
    }
  }
  if (expect.bisectMessageIncludes) {
    const found = state.bisect?.current
    const message = found ? state.commits[found]?.message || '' : ''
    if (!message.includes(expect.bisectMessageIncludes)) {
      return {
        passed: false,
        feedback: `bisect: ожидали commit с «${expect.bisectMessageIncludes}», получили «${message}»`,
      }
    }
  }
  return { passed: true, feedback: 'совпало' }
}

export function runGitWithCheck(
  studentScript: string,
  seedScript: string,
  expect: GitCheckExpect,
): GitRunResult & { passed: boolean; feedback: string } {
  const seeded = runGitScript(seedScript)
  if (!seeded.ok) {
    return {
      ...seeded,
      passed: false,
      feedback: `FAIL seed: ${seeded.stderr}`,
    }
  }
  const run = runGitScript(studentScript, seeded.state)
  if (!run.ok) {
    return {
      ...run,
      passed: false,
      feedback: `FAIL: ${run.stderr}`,
    }
  }
  const cmp = checkGitState(run.state, expect)
  return {
    ...run,
    passed: cmp.passed,
    feedback: cmp.passed ? `PASS: ${cmp.feedback}` : `FAIL: ${cmp.feedback}`,
  }
}

export function formatGitChannels(run: GitRunResult): string {
  const parts: string[] = []
  if (run.stdout) parts.push(run.stdout)
  if (run.stderr) parts.push(`ERROR: ${run.stderr}`)
  if (!parts.length) parts.push('(ok)')
  const snap = [
    '',
    '--- repo ---',
    statusText(run.state).split('\n').slice(0, 8).join('\n'),
  ]
  return [...parts, ...snap].join('\n')
}

const BASH_FENCE = /```(?:bash|sh|shell)\s*\n([\s\S]*?)```/gi

/** Extract fenced bash/sh blocks that look like git scripts. */
export function extractGitBlocks(markdown: string): string[] {
  const blocks: string[] = []
  const re = new RegExp(BASH_FENCE.source, 'gi')
  let match: RegExpExecArray | null
  while ((match = re.exec(markdown || '')) !== null) {
    const code = match[1].replace(/\s+$/, '')
    if (code.trim() && /\bgit\b/.test(code)) {
      blocks.push(code)
    }
  }
  return blocks
}

export function snapshotPanel(state: GitState): string {
  const branch =
    state.head.type === 'branch' ? state.head.name : `detached:${state.head.hash.slice(0, 7)}`
  const log = runGitScript('git log --oneline', state).stdout
  return `branch: ${branch}\n\n${log || '(no commits)'}`
}
