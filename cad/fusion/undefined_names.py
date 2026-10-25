"""Fail on names a module uses but never defines (the pre-commit hook runs it on cad/fusion/*.py and cad/sim/*.py).

Fusion reloads modules with importlib.reload, which keeps a module's old globals: a constant deleted from the source
(gripper3.MU_SLIDE, 25 Oct) went on working inside Fusion and failed only in a fresh session. This finds such names
without running anything: every global a function reads must be defined at module level, imported, or a builtin.

    python cad/fusion/undefined_names.py file.py [...]     # exit 1 and a list if any
"""
import builtins
import sys
import symtable


def undefined(path):
    src = open(path, encoding='utf-8').read()
    top = symtable.symtable(src, path, 'exec')
    defined = {s.get_name() for s in top.get_symbols() if s.is_assigned() or s.is_imported()}
    if any(s.get_name() == '*' for s in top.get_symbols()):
        return []                                           # star import: can't tell
    known = defined | set(dir(builtins)) | {'__file__', '__name__', '__doc__'}
    bad = []

    def walk(t):
        for ch in t.get_children():
            for s in ch.get_symbols():
                if s.is_global() and s.is_referenced() and not s.is_declared_global() and s.get_name() not in known:
                    bad.append((ch.get_name(), ch.get_lineno(), s.get_name()))
                elif s.is_declared_global() and s.is_referenced() and s.get_name() not in known and not s.is_assigned():
                    bad.append((ch.get_name(), ch.get_lineno(), s.get_name()))
            walk(ch)
    walk(top)
    return bad


if __name__ == '__main__':
    n = 0
    for f in sys.argv[1:]:
        for fn, line, name in undefined(f):
            print('%s:%d: %s uses %s, which is defined nowhere' % (f, line, fn, name))
            n += 1
    sys.exit(1 if n else 0)
