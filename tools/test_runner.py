"""
Module to identify all unit tests that need to run and return a TestSuite object to be run
"""

import os
import sys
import site
import unittest
import logging
import re
import types

pt = os.getcwd()
root_dir = pt
loglevel = int(os.environ.get('UNITTEST_LOGLEVEL', logging.CRITICAL))
logging.getLogger().setLevel(loglevel) # DEBUG, LOG, WARN, ERROR(?) are too chatty

TEST_MODULES = [
    'test',
]

COVERAGE_OMIT_PATHS = [
    'test/*',
    'src/lib/*',
    'src/app/views/*',
    'tools/*',
    '/usr/local/google_appengine/*' ,
    'C:\Program Files (x86)\Google\google_appengine/*',
    '/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/*'
]

def convert_module_path(module):
    """
    Helper method to convert a module in dot notation toa proper file path
    """
    path_bits = module.split(".")
    return os.path.sep.join(path_bits)

def printDbg(msg):
    """
    Funnel debug printing through this method for simple enable/disable
    """
#    print msg
    pass

def suite(testsReg):
    """
    Iterate across all of the modules in TEST_MODULES, find all of the
    tests within and return a TestSuite which will run them all

    Args:
        pattern is regular expression specified for file pattern
    """

    assert testsReg
    for p in sys.path:
        printDbg("PATH --> %s" % p)

    try:
        test_suite = unittest.TestSuite()
        TEST_RE = testsReg
        test_names = []
        # Search through every file inside this package.
        for module in TEST_MODULES:
            printDbg("Considering TEST MODULE: '%s'" % module)
            test_dir = os.path.join(root_dir, convert_module_path(module))
            for filename in os.listdir(test_dir):
                if os.path.isdir(os.path.join(test_dir, filename)) and not filename.startswith("."):
                    newModule = module + "." + filename
                    printDbg("-- Appending sub module: '%s'" % newModule)
                    TEST_MODULES.append(newModule)
                    continue
                if not re.match(TEST_RE, filename):
                    printDbg("-- Skipping file '%s'" % filename)
                    continue
                # Import the test file and find all TestClass clases inside it.
                leaf = filename[:-3]
                module_name = '%s.%s' % (module, leaf)
                printDbg("----> Importing '%s' (%s)" % (module_name, leaf))
                test_module = __import__(module_name, {}, {}, leaf)
                test_suite.addTest(unittest.TestLoader().loadTestsFromModule(test_module))
        return test_suite
    except Exception:
        logging.critical("Error loading tests.", exc_info=True)
        raise SystemExit("Error loading tests.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # tests specified
        name = str(sys.argv[1])
        if '/' in name:
            name = name.replace('.py', '')
            name = name.replace('/', '.')
        tests = name.split(',')
        test_suite = unittest.TestLoader().loadTestsFromNames(tests) # specific test(s)
    else:
        test_suite = suite(r"^.*_tests?\.py$") # all unit tests
    unittest.TextTestRunner(verbosity=int(os.environ.get('UNITTEST_VERBOSITY', 1))).run(test_suite)
