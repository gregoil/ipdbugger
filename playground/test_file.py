from ipdbugger import debug

@debug
def a():
    raise NotImplementedError

a()
