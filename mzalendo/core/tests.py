from django.utils import unittest

def suite():
    """Load all test_*.py files"""
    suite = unittest.TestLoader().discover( '.', pattern='tests_*.py' )
    return suite