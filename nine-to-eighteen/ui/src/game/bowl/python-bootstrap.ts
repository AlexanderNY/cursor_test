export const ENGINE_BOOTSTRAP = `
import sys
if "/bowl/py" not in sys.path:
    sys.path.insert(0, "/bowl/py")
from game_engine import engine
`.trim()
