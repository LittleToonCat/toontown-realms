"""
Global module specifically to make developing using IDEs much better

"""


try:
    base = base
    loader = base.loader
    render = base.render
except:
    base = None
