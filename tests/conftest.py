from   os.path import dirname, abspath, splitext, join, basename
import pytest
from   sidetrack import set_debug


@pytest.fixture(scope="module", autouse=True)
def saver_debug_log(request):
    '''Turn on debug logging & save the output to "testfile.log".'''
    here = dirname(abspath(__file__))
    mod_name = request.module.__name__
    log_file = join(here, splitext(basename(mod_name))[0] + '.log')
    open(log_file, 'w').close()
    set_debug(True, log_file)
    yield
