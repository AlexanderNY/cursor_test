import type { GitCheckExpect } from '@/game/git/sandbox-git'

export type GitTask = {
  id: string
  title: string
  episode: string
  learnSlug: string
  level: 'junior' | 'middle'
  prompt: string
  examples: string[]
  /** Applied before student script on a fresh repo. */
  seedCommands: string
  starterCommands: string
  check: GitCheckExpect
}

export const GIT_TASKS: GitTask[] = [
  {
    id: 'init-commit',
    title: 'init + first commit',
    episode: 'GIT01',
    learnSlug: 'git-commit-anatomy',
    level: 'junior',
    prompt:
      'Инициализируйте репозиторий, добавьте README.md со строкой hello и сделайте commit с сообщением, содержащим init.',
    examples: ['git init', 'write README.md hello', 'git add README.md', 'git commit -m "init: …"'],
    seedCommands: '',
    starterCommands: `# git init
# write README.md hello
# git add …
# git commit -m "init: notes"
`,
    check: {
      branch: 'main',
      headFiles: { 'README.md': 'hello' },
      headMessageIncludes: 'init',
    },
  },
  {
    id: 'stage-index',
    title: 'Только один файл в index',
    episode: 'S01E03',
    learnSlug: 's01e03-git',
    level: 'junior',
    prompt:
      'В рабочей копии уже a.txt и b.txt. Добавьте в index только a.txt (b.txt остаётся untracked/не в index).',
    examples: ['git add a.txt', 'не add b.txt'],
    seedCommands: `git init
write a.txt aaa
write b.txt bbb
`,
    starterCommands: `# git add …
`,
    check: {
      indexPaths: ['a.txt'],
      indexMissing: ['b.txt'],
      workTreePaths: ['a.txt', 'b.txt'],
    },
  },
  {
    id: 'branch-switch',
    title: 'Ветка и commit',
    episode: 'B06',
    learnSlug: 'b05-api-check',
    level: 'junior',
    prompt:
      'Создайте ветку feature, переключитесь на неё, добавьте docs.md и закоммитьте. HEAD должен быть на feature.',
    examples: ['git switch -c feature', 'write docs.md …', 'git add', 'git commit'],
    seedCommands: `git init
write README.md base
git add README.md
git commit -m "init"
`,
    starterCommands: `git switch -c feature
write docs.md layers
git add docs.md
git commit -m "docs: layers"
`,
    check: {
      branch: 'feature',
      headFiles: { 'README.md': 'base', 'docs.md': 'layers' },
      headMessageIncludes: 'docs',
    },
  },
  {
    id: 'branch-rename',
    title: 'Переименовать ветку',
    episode: 'GIT02',
    learnSlug: 'git-commit-anatomy',
    level: 'junior',
    prompt: 'Переименуйте текущую ветку old-name в new-name через git branch -m.',
    examples: ['git branch -m new-name'],
    seedCommands: `git init
write README.md x
git add README.md
git commit -m "init"
git branch -m old-name
`,
    starterCommands: `git branch -m new-name
`,
    check: {
      branch: 'new-name',
    },
  },
  {
    id: 'remote-set-url',
    title: 'remote add + set-url',
    episode: 'GIT02',
    learnSlug: 'git-commit-anatomy',
    level: 'junior',
    prompt:
      'Добавьте remote origin с любым URL, затем смените URL на https://github.com/you/notes.git',
    examples: [
      'git remote add origin https://example.com/old.git',
      'git remote set-url origin https://github.com/you/notes.git',
    ],
    seedCommands: `git init
write README.md x
git add README.md
git commit -m "init"
`,
    starterCommands: `# git remote add origin …
# git remote set-url origin https://github.com/you/notes.git
`,
    check: {
      remotes: { origin: 'https://github.com/you/notes.git' },
    },
  },
  {
    id: 'fetch-vs-pull',
    title: 'pull подтягивает remote',
    episode: 'GIT02',
    learnSlug: 'git-commit-anatomy',
    level: 'middle',
    prompt:
      'Remote origin уже впереди (есть remote-only.txt). Сделайте git pull origin, чтобы файл появился в HEAD.',
    examples: ['git pull origin', 'после pull в HEAD есть remote-only.txt'],
    seedCommands: `git init
write README.md base
git add README.md
git commit -m "init"
seed-remote origin https://example.com/repo.git main
seed-remote-ahead origin
`,
    starterCommands: `git pull origin
`,
    check: {
      headFiles: { 'README.md': 'base', 'remote-only.txt': 'from remote' },
    },
  },
  {
    id: 'stash-roundtrip',
    title: 'stash → clean → pop',
    episode: 'GIT03',
    learnSlug: 'git-commit-anatomy',
    level: 'junior',
    prompt:
      'Есть грязный worktree (dirty.txt). Сделайте stash так, чтобы working tree стал clean и stashCount=1. Не делайте pop в этом задании.',
    examples: ['git stash'],
    seedCommands: `git init
write README.md base
git add README.md
git commit -m "init"
write dirty.txt wip
`,
    starterCommands: `git stash
`,
    check: {
      stashCount: 1,
      workTreeMissing: ['dirty.txt'],
    },
  },
  {
    id: 'reset-soft-local',
    title: 'reset HEAD~ (mixed)',
    episode: 'GIT03',
    learnSlug: 'git-commit-anatomy',
    level: 'middle',
    prompt:
      'Отмените последний локальный commit через git reset HEAD~. Файл extra.txt должен остаться в working tree, но не в HEAD.',
    examples: ['git reset HEAD~'],
    seedCommands: `git init
write README.md base
git add README.md
git commit -m "init"
write extra.txt more
git add extra.txt
git commit -m "add extra"
`,
    starterCommands: `git reset HEAD~
`,
    check: {
      headMissingFiles: ['extra.txt'],
      workTreePaths: ['extra.txt'],
      headFiles: { 'README.md': 'base' },
    },
  },
  {
    id: 'rm-cached',
    title: 'rm --cached',
    episode: 'GIT03',
    learnSlug: 'git-commit-anatomy',
    level: 'junior',
    prompt:
      'Уберите secret.env из index через git rm --cached, но файл должен остаться в working tree.',
    examples: ['git rm --cached secret.env'],
    seedCommands: `git init
write README.md ok
write secret.env KEY=1
git add README.md secret.env
git commit -m "init with secret"
`,
    starterCommands: `git rm --cached secret.env
`,
    check: {
      indexMissing: ['secret.env'],
      workTreePaths: ['secret.env'],
    },
  },
  {
    id: 'merge-feature',
    title: 'merge feature → main',
    episode: 'GIT04',
    learnSlug: 'git-commit-anatomy',
    level: 'junior',
    prompt: 'Смержите ветку feature в main (сейчас вы на main).',
    examples: ['git merge feature'],
    seedCommands: `git init
write README.md base
git add README.md
git commit -m "init"
git switch -c feature
write feature.txt yes
git add feature.txt
git commit -m "feat: add feature"
git switch main
`,
    starterCommands: `git merge feature
`,
    check: {
      branch: 'main',
      headFiles: { 'README.md': 'base', 'feature.txt': 'yes' },
      merged: ['feature'],
    },
  },
  {
    id: 'tag-release',
    title: 'Создать tag',
    episode: 'GIT05',
    learnSlug: 'git-commit-anatomy',
    level: 'junior',
    prompt: 'Поставьте тег v1.0 на текущий HEAD.',
    examples: ['git tag v1.0', 'или git tag -a v1.0 -m "release"'],
    seedCommands: `git init
write README.md base
git add README.md
git commit -m "init"
`,
    starterCommands: `git tag v1.0
`,
    check: {
      tags: ['v1.0'],
    },
  },
  {
    id: 'bisect-find',
    title: 'bisect: первый bad',
    episode: 'GIT05',
    learnSlug: 'git-commit-anatomy',
    level: 'middle',
    prompt:
      'Цепочка уже в репо. Запустите git bisect start, отметьте HEAD как bad, а commit good0 как good. Симулятор найдёт первый bad.',
    examples: [
      'git bisect start',
      'git bisect bad',
      'git bisect good <hash-good0>',
    ],
    seedCommands: `git init
write app.txt good
git add app.txt
git commit -m "good0"
write app.txt still-good
git add app.txt
git commit -m "good1"
write app.txt broken
git add app.txt
git commit -m "bad-intro"
write app.txt still-broken
git add app.txt
git commit -m "bad-later"
`,
    starterCommands: `git bisect start
git bisect bad
git bisect good HEAD~2
`,
    check: {
      bisectMessageIncludes: 'bad-intro',
    },
  },
]

const byId = new Map(GIT_TASKS.map((task) => [task.id, task]))

export function getGitTask(id: string): GitTask | undefined {
  return byId.get(id)
}

export function gitTasksByEpisode(episode: string): GitTask[] {
  return GIT_TASKS.filter(
    (task) => task.episode.toUpperCase() === episode.toUpperCase(),
  )
}

export function gitTasksForLearnSlug(slug: string): GitTask[] {
  return GIT_TASKS.filter((task) => task.learnSlug === slug)
}

const RELATED: Record<string, string[]> = {
  'b01-karta': ['init-commit', 'stage-index'],
  'b05-api-check': ['branch-switch', 'merge-feature'],
  's01e03-git': ['init-commit', 'stage-index', 'branch-switch'],
  'qa-pytest-ci-git': ['stash-roundtrip', 'branch-switch'],
  'git-commit-anatomy': [
    'init-commit',
    'stage-index',
    'remote-set-url',
    'fetch-vs-pull',
    'branch-rename',
    'stash-roundtrip',
    'reset-soft-local',
    'rm-cached',
    'merge-feature',
    'tag-release',
    'bisect-find',
  ],
}

export function gitTasksForLearnEpisode(
  episode: string,
  slug: string,
): { tasks: GitTask[]; related: boolean } {
  const direct = [
    ...gitTasksByEpisode(episode),
    ...gitTasksForLearnSlug(slug),
  ]
  const seen = new Set<string>()
  const unique = direct.filter((task) => {
    if (seen.has(task.id)) return false
    seen.add(task.id)
    return true
  })
  if (unique.length > 0) {
    return { tasks: unique, related: false }
  }
  const ids = RELATED[slug] || []
  const tasks = ids
    .map((id) => getGitTask(id))
    .filter((task): task is GitTask => Boolean(task))
  return { tasks, related: tasks.length > 0 }
}
