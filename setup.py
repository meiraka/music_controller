import sys
import os

def unittest():
	import unittest
	project_dir = os.path.dirname(os.path.abspath(__file__))
	sys.path.extend([project_dir+'/src',project_dir+'/tests'])
	tests = ['client_test']
	for test in tests:
		module = __import__(test)
		test_cases = [getattr(module,class_name) for class_name in dir(module) if class_name.startswith('Test')]
		for test_case in test_cases:
			suite = unittest.TestLoader().loadTestsFromTestCase(test_case)
			unittest.TextTestRunner(verbosity=2).run(suite)


if sys.argv.count('test'):
	del sys.argv[sys.argv.index('test')]
	unittest()
