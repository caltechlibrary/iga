'''
exceptions.py: exceptions for IGA

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022-2024 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''


# Base class.
# .............................................................................
# The base class makes it possible to use a single test to distinguish between
# exceptions generated by IGA and exceptions generated by something else.

class IGAException(Exception):
    '''Base class for IGA exceptions.'''


# Exception classes.
# .............................................................................

class GitHubError(IGAException):
    '''GitHub returned an error.'''


class InvenioRDMError(IGAException):
    '''InvenioRDM returned an error.'''


class BadToken(IGAException):
    '''Invalid personal access token.'''


class MissingData(IGAException):
    '''Could not obtain all the required data to create an InvenioRDM record.'''


class RecordNotFound(IGAException):
    '''Could not find the requested record in the InvenioRDM server.'''


class InternalError(IGAException):
    '''An internal error occurred in IGA.'''
