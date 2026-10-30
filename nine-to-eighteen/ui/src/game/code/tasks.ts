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
    learnSlug: 'py-intro-python',
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
    learnSlug: 'py-intro-python',
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
    learnSlug: 'py-strings-ops-io',
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
    learnSlug: 'py-strings-ops-io',
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
    learnSlug: 'py-strings-ops-io',
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
    learnSlug: 'py-oop-basics',
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
    learnSlug: 'py-oop-basics',
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
    learnSlug: 'py-oop-basics',
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
    learnSlug: 'py-strings-ops-io',
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
  {
    id: 'mutable-default',
    title: 'Общий список по умолчанию',
    episode: 'PY01',
    learnSlug: 'py-intro-python',
    level: 'junior',
    prompt:
      'Почините append_item(item, bucket=None) -> list. Два вызова без bucket не должны делить один список.',
    examples: ['append_item(1) → [1]', 'следующий append_item(2) → [2], не [1, 2]'],
    starterCode: `def append_item(item, bucket=[]):
    bucket.append(item)
    return bucket
`,
    checker: `
def __check():
    first = append_item("a")
    second = append_item("b")
    if first == ["a"] and second == ["b"]:
        print("PASS: у каждого вызова свой список")
        return
    print(f"FAIL: append_item вернул {first!r} и {second!r}. Значение по умолчанию создаётся один раз")

__check()
`,
  },
  {
    id: 'is-vs-eq',
    title: 'is и ==',
    episode: 'PY01',
    learnSlug: 'py-intro-python',
    level: 'junior',
    prompt:
      'Напишите same_value(left, right) -> bool и same_object(left, right) -> bool. Первая сравнивает значение, вторая — один ли это объект.',
    examples: ['same_value([1], [1]) → True', 'same_object([1], [1]) → False'],
    starterCode: `def same_value(left, right) -> bool:
    ...

def same_object(left, right) -> bool:
    ...
`,
    checker: `
def __check():
    if same_value([1], [1]) is not True or same_value(1, 2) is not False:
        print("FAIL: same_value должна сравнивать значения")
        return
    left = []
    if same_object(left, left) is not True or same_object([1], [1]) is not False:
        print("FAIL: same_object должна проверять идентичность, не равенство")
        return
    if same_value(None, None) is not True or same_object(None, None) is not True:
        print("FAIL: None и равен, и тот же объект")
        return
    print("PASS: == и is разведены")

__check()
`,
  },
  {
    id: 'dict-key',
    title: 'Ключ словаря',
    episode: 'PY01',
    learnSlug: 'py-intro-python',
    level: 'junior',
    prompt:
      'Напишите point_key(x: int, y: int), чтобы координату можно было положить ключом в dict. Список ключом быть не может.',
    examples: ['points = {point_key(1, 2): "A"}'],
    starterCode: `def point_key(x: int, y: int):
    # TODO: верните hashable-координату
    ...
`,
    checker: `
def __check():
    key = point_key(1, 2)
    try:
        hash(key)
    except TypeError:
        print(f"FAIL: {key!r} нельзя положить в dict")
        return
    points = {key: "A", point_key(1, 2): "B"}
    if points[point_key(1, 2)] != "B" or len(points) != 1:
        print("FAIL: одинаковые координаты должны быть одним ключом")
        return
    print("PASS: координата годится в ключ")

__check()
`,
  },
  {
    id: 'n-plus-one',
    title: 'Один запрос вместо N',
    episode: 'PY27',
    learnSlug: 'py-sqlalchemy',
    level: 'junior',
    prompt:
      'Напишите load_titles(ids: list[int]) -> list[str]. query_one считает запрос на каждый id, query_many — один запрос на весь список. На пяти id должен случиться один вызов query_many и ни одного query_one.',
    examples: ['load_titles([1, 2]) → ["t1", "t2"]'],
    starterCode: `CALLS = {"one": 0, "many": 0}

def query_one(order_id: int) -> str:
    CALLS["one"] += 1
    return f"t{order_id}"

def query_many(order_ids: list[int]) -> list[str]:
    CALLS["many"] += 1
    return [f"t{order_id}" for order_id in order_ids]

def load_titles(ids: list[int]) -> list[str]:
    # TODO: не вызывайте query_one в цикле
    ...
`,
    checker: `
def __check():
    CALLS["one"] = 0
    CALLS["many"] = 0
    got = load_titles([1, 2, 3, 4, 5])
    if got != ["t1", "t2", "t3", "t4", "t5"]:
        print(f"FAIL: {got!r}")
        return
    if CALLS["one"] != 0 or CALLS["many"] != 1:
        print(f"FAIL: query_one={CALLS['one']}, query_many={CALLS['many']}. Нужен один query_many")
        return
    print("PASS: N+1 снят")

__check()
`,
  },
  {
    id: 'review-split',
    title: 'Два шва вместо одной функции',
    episode: 'PY26',
    learnSlug: 'py-code-review',
    level: 'junior',
    prompt:
      'Разнесите закрытие заявки. save_ticket(ticket_id) -> str возвращает "saved:<id>". notify(ticket_id) -> str возвращает "sent:<id>". close_ticket(ticket_id) -> tuple[str, str] вызывает обе и возвращает пару.',
    examples: ['close_ticket("a") → ("saved:a", "sent:a")'],
    starterCode: `def close_ticket(ticket_id: str):
    saved = "saved:" + ticket_id
    sent = "sent:" + ticket_id
    return saved, sent
`,
    checker: `
def __check():
    for name in ("save_ticket", "notify", "close_ticket"):
        if name not in globals() or not callable(globals()[name]):
            print(f"FAIL: нет функции {name}")
            return
    if save_ticket("a") != "saved:a" or notify("a") != "sent:a":
        print("FAIL: save_ticket и notify должны возвращать saved: и sent:")
        return
    if close_ticket("a") != ("saved:a", "sent:a"):
        print(f"FAIL: close_ticket вернул {close_ticket('a')!r}")
        return
    print("PASS: сохранение и письмо разведены")

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
