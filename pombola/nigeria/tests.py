import unittest
import doctest
from . import views

# Needed to run the doc tests in views.py

def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(views))
    return suite