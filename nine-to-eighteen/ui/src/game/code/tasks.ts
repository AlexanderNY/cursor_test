export type CodeTask = {
  id: string
  title: string
  episode: string
  learnSlug: string
  level: 'junior'
  prompt: string
  examples: string[]
  starterCode: string
  /** Python that prints PASS:… or FAIL:… after student code. */
  checker: string
}

export const CODE_TASKS: CodeTask[] = [
  {
    id: 'word-freq',
    title: 'Частоты слов',
    episode: 'PY02',
    learnSlug: 'py-types-collections',
    level: 'junior',
    prompt:
      'Напишите функцию word_freq(words: list[str]) -> dict[str, int]: число вхождений каждого слова. Порядок ключей не важен.',
    examples: [
      'word_freq(["a", "b", "a"]) → {"a": 2, "b": 1}',
      'word_freq([]) → {}',
    ],
    starterCode: `def word_freq(words: list[str]) -> dict[str, int]:
    # TODO: посчитайте частоты
    ...
`,
    checker: `
def __check():
    cases = [
        (["a", "b", "a"], {"a": 2, "b": 1}),
        ([], {}),
        (["x", "x", "x"], {"x": 3}),
        (["Hi", "hi"], {"Hi": 1, "hi": 1}),
    ]
    for words, expected in cases:
        got = word_freq(words)
        if got != expected:
            print(f"FAIL: word_freq({words!r}) → {got!r}, ожидалось {expected!r}")
            return
    print("PASS: все тесты word_freq")

__check()
`,
  },
  {
    id: 'unique-preserve',
    title: 'Уникальные с сохранением порядка',
    episode: 'PY02',
    learnSlug: 'py-types-collections',
    level: 'junior',
    prompt:
      'Напишите unique_preserve(items: list) -> list: первое вхождение каждого элемента, без set→list (порядок set не гарантирован).',
    examples: ['unique_preserve([1, 2, 1, 3, 2]) → [1, 2, 3]'],
    starterCode: `def unique_preserve(items: list) -> list:
    # TODO
    ...
`,
    checker: `
def __check():
    cases = [
        ([1, 2, 1, 3, 2], [1, 2, 3]),
        ([], []),
        (["a", "a", "b"], ["a", "b"]),
    ]
    for items, expected in cases:
        got = unique_preserve(items)
        if got != expected:
            print(f"FAIL: unique_preserve({items!r}) → {got!r}, ожидалось {expected!r}")
            return
    print("PASS: порядок первых вхождений сохранён")

__check()
`,
  },
  {
    id: 'join-words',
    title: 'Сборка строки через join',
    episode: 'PY03',
    learnSlug: 'py-strings-ops-io',
    level: 'junior',
    prompt:
      'Напишите join_words(parts: list[str], sep: str = " ") -> str без цикла с += для склейки (используйте str.join).',
    examples: ['join_words(["a", "b", "c"], "-") → "a-b-c"'],
    starterCode: `def join_words(parts: list[str], sep: str = " ") -> str:
    # TODO: return sep.join(...)
    ...
`,
    checker: `
def __check():
    cases = [
        (["a", "b", "c"], "-", "a-b-c"),
        ([], " ", ""),
        (["one"], ",", "one"),
        (["x", "y"], " ", "x y"),
    ]
    for parts, sep, expected in cases:
        got = join_words(parts, sep)
        if got != expected:
            print(f"FAIL: join_words({parts!r}, {sep!r}) → {got!r}, ожидалось {expected!r}")
            return
    print("PASS: join_words")

__check()
`,
  },
  {
    id: 'normalize-lines',
    title: 'Нормализация строк',
    episode: 'PY03',
    learnSlug: 'py-strings-ops-io',
    level: 'junior',
    prompt:
      'Напишите normalize_lines(text: str) -> list[str]: разбить по строкам, strip каждой, отбросить пустые.',
    examples: ['normalize_lines("  a\\n\\n b ") → ["a", "b"]'],
    starterCode: `def normalize_lines(text: str) -> list[str]:
    # TODO
    ...
`,
    checker: `
def __check():
    cases = [
        ("  a\\n\\n b ", ["a", "b"]),
        ("", []),
        ("x", ["x"]),
        ("\\n\\n", []),
    ]
    for text, expected in cases:
        got = normalize_lines(text)
        if got != expected:
            print(f"FAIL: normalize_lines({text!r}) → {got!r}, ожидалось {expected!r}")
            return
    print("PASS: normalize_lines")

__check()
`,
  },
  {
    id: 'group-by-len',
    title: 'Группировка по длине',
    episode: 'PY04',
    learnSlug: 'py-control-flow-functions',
    level: 'junior',
    prompt:
      'Напишите group_by_len(*words: str, upper: bool = False) -> dict[int, list[str]]. Ключ — длина слова; при upper=True слова в верхнем регистре. Не используйте mutable default.',
    examples: [
      'group_by_len("hi", "hey", "a") → {2: ["hi"], 3: ["hey"], 1: ["a"]}',
      'group_by_len("hi", upper=True) → {2: ["HI"]}',
    ],
    starterCode: `def group_by_len(*words: str, upper: bool = False) -> dict[int, list[str]]:
    # TODO
    ...
`,
    checker: `
def __check():
    got = group_by_len("hi", "hey", "a")
    expected = {2: ["hi"], 3: ["hey"], 1: ["a"]}
    if got != expected:
        print(f"FAIL: {got!r} != {expected!r}")
        return
    got2 = group_by_len("hi", "ab", upper=True)
    if got2 != {2: ["HI", "AB"]}:
        print(f"FAIL: upper={got2!r}")
        return
    if group_by_len() != {}:
        print("FAIL: пустой вызов должен давать {}")
        return
    print("PASS: group_by_len")

__check()
`,
  },
  {
    id: 'safe-default',
    title: 'Без mutable default',
    episode: 'PY04',
    learnSlug: 'py-control-flow-functions',
    level: 'junior',
    prompt:
      'Напишите append_item(value, acc=None) -> list: добавляет value в список и возвращает его. Дефолт acc должен быть безопасным (None), чтобы вызовы не делили один список.',
    examples: [
      'append_item(1); append_item(2) → второй вызов даёт [2], не [1, 2]',
    ],
    starterCode: `def append_item(value, acc=None):
    # TODO: if acc is None: acc = []
    ...
`,
    checker: `
def __check():
    a = append_item(1)
    b = append_item(2)
    if a == [1, 2] or b == [1, 2]:
        print("FAIL: похоже на mutable default — вызовы делят список")
        return
    if a != [1] or b != [2]:
        print(f"FAIL: ожидали [1] и [2], получили {a!r} и {b!r}")
        return
    c = append_item(3, [0])
    if c != [0, 3]:
        print(f"FAIL: с явным acc ожидали [0, 3], получили {c!r}")
        return
    print("PASS: безопасный default")

__check()
`,
  },
  {
    id: 'public-names',
    title: 'Публичные имена модуля',
    episode: 'PY05',
    learnSlug: 'py-modules-packages-venv',
    level: 'junior',
    prompt:
      'Напишите public_names(mapping: dict[str, object]) -> list[str]: имена без ведущего «_», отсортированные.',
    examples: ['public_names({"_x": 1, "y": 2, "a": 3}) → ["a", "y"]'],
    starterCode: `def public_names(mapping: dict[str, object]) -> list[str]:
    # TODO
    ...
`,
    checker: `
def __check():
    got = public_names({"_x": 1, "y": 2, "a": 3, "__d__": 0})
    if got != ["a", "y"]:
        print(f"FAIL: {got!r}")
        return
    if public_names({}) != []:
        print("FAIL: пустой dict")
        return
    print("PASS: public_names")

__check()
`,
  },
  {
    id: 'rectangle-area',
    title: 'Площадь прямоугольника',
    episode: 'PY06',
    learnSlug: 'py-oop-basics',
    level: 'junior',
    prompt:
      'Класс Rectangle с __init__(self, width, height) и методом area(self) -> число. Ширина и высота > 0, иначе ValueError.',
    examples: ['Rectangle(3, 4).area() → 12'],
    starterCode: `class Rectangle:
    def __init__(self, width, height):
        # TODO
        ...

    def area(self):
        # TODO
        ...
`,
    checker: `
def __check():
    r = Rectangle(3, 4)
    if r.area() != 12:
        print(f"FAIL: area={r.area()!r}")
        return
    try:
        Rectangle(0, 2)
        print("FAIL: ожидался ValueError при width=0")
        return
    except ValueError:
        pass
    try:
        Rectangle(2, -1)
        print("FAIL: ожидался ValueError при height<0")
        return
    except ValueError:
        pass
    print("PASS: Rectangle")

__check()
`,
  },
  {
    id: 'parse-positive',
    title: 'parse_positive',
    episode: 'PY07',
    learnSlug: 'py-exceptions',
    level: 'junior',
    prompt:
      'Напишите parse_positive(text: str) -> int: целое > 0. Невалидный текст или число ≤ 0 → ValueError.',
    examples: [
      'parse_positive("12") → 12',
      'parse_positive("0") и parse_positive("x") → ValueError',
    ],
    starterCode: `def parse_positive(text: str) -> int:
    # TODO
    ...
`,
    checker: `
def __check():
    if parse_positive("12") != 12:
        print("FAIL: '12'")
        return
    for bad in ("0", "-3", "x", "3.5", ""):
        try:
            parse_positive(bad)
            print(f"FAIL: для {bad!r} ожидали ValueError")
            return
        except ValueError:
            pass
    print("PASS: parse_positive")

__check()
`,
  },
  {
    id: 'filter-emails',
    title: 'Фильтр email regex',
    episode: 'PY08',
    learnSlug: 'py-stdlib-re-json-copy',
    level: 'junior',
    prompt:
      'Напишите filter_emails(items: list[str]) -> list[str]: строки, целиком похожие на простой email (буквы/цифры/._+ до @, домен с точкой). Используйте re.fullmatch.',
    examples: [
      'filter_emails(["a@b.co", "nope", "x@y.z"]) → ["a@b.co", "x@y.z"]',
    ],
    starterCode: `import re

def filter_emails(items: list[str]) -> list[str]:
    # TODO: pattern + fullmatch
    ...
`,
    checker: `
def __check():
    got = filter_emails(["a@b.co", "nope", "x@y.z", "@bad.com", "a@b"])
    expected = ["a@b.co", "x@y.z"]
    if got != expected:
        print(f"FAIL: {got!r}, ожидалось {expected!r}")
        return
    if filter_emails([]) != []:
        print("FAIL: пустой список")
        return
    print("PASS: filter_emails")

__check()
`,
  },
  {
    id: 'deep-meta-copy',
    title: 'Deep copy meta',
    episode: 'PY08',
    learnSlug: 'py-stdlib-re-json-copy',
    level: 'junior',
    prompt:
      'Напишите clone_user(user: dict) -> dict: глубокая копия (copy.deepcopy), чтобы правка clone["meta"]["role"] не меняла оригинал.',
    examples: ['после clone["meta"]["role"]="x" оригинал не меняется'],
    starterCode: `import copy

def clone_user(user: dict) -> dict:
    # TODO
    ...
`,
    checker: `
def __check():
    original = {"name": "Ada", "meta": {"role": "dev"}}
    cloned = clone_user(original)
    cloned["meta"]["role"] = "admin"
    if original["meta"]["role"] != "dev":
        print("FAIL: оригинал изменился — нужна deepcopy")
        return
    if cloned["meta"]["role"] != "admin":
        print("FAIL: клон не изменился")
        return
    print("PASS: deepcopy")

__check()
`,
  },
  {
    id: 'first-even',
    title: 'Первое чётное (for/else)',
    episode: 'PY04',
    learnSlug: 'py-control-flow-functions',
    level: 'junior',
    prompt:
      'Напишите first_even(nums: list[int]) -> int | None: первое чётное или None. Используйте for/else (без флага found).',
    examples: ['first_even([1, 3, 4, 6]) → 4', 'first_even([1, 3]) → None'],
    starterCode: `def first_even(nums: list[int]):
    # TODO: for … else
    ...
`,
    checker: `
def __check():
    if first_even([1, 3, 4, 6]) != 4:
        print("FAIL: первое чётное")
        return
    if first_even([1, 3]) is not None:
        print("FAIL: ожидался None")
        return
    if first_even([]) is not None:
        print("FAIL: пустой список")
        return
    print("PASS: first_even")

__check()
`,
  },
]

export function getCodeTask(id: string): CodeTask | undefined {
  return CODE_TASKS.find((task) => task.id === id)
}

export function codeTasksByEpisode(): Map<string, CodeTask[]> {
  const map = new Map<string, CodeTask[]>()
  for (const task of CODE_TASKS) {
    const list = map.get(task.episode) ?? []
    list.push(task)
    map.set(task.episode, list)
  }
  return map
}
