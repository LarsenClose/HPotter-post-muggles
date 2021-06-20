''' Wrap an __init__ function so that I don't have to assign all the
parameters to a self. variable. '''
# https://stackoverflow.com/questions/5048329/python-decorator-for-automatic-binding-init-arguments

import inspect

from functools import wraps

def lazy_init(init):
    ''' Create an annotation to assign all the parameters to a self.
    variable. '''
    arg_names = inspect.getfullargspec(init)[0]

    # pylint: disable=E1101
    @wraps(init)
    def new_init(self, *args):
        for name, value in zip(arg_names[1:], args):
            setattr(self, name, value)
        init(self, *args)

    return new_init
