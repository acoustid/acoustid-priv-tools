# This file is part of pyacoustid.
# Copyright 2014, Adrian Sampson.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

import os
import errno
import subprocess

FPCALC_COMMAND = 'fpcalc'
FPCALC_ENVVAR = 'FPCALC'


class ChromaprintError(Exception):
    """Base for exceptions in this module."""


class FingerprintGenerationError(ChromaprintError):
    """The audio could not be fingerprinted."""


class NoBackendError(FingerprintGenerationError):
    """The audio could not be fingerprinted because neither the
    Chromaprint library nor the fpcalc command-line tool is installed.
    """


def fingerprint_file_fpcalc(path, maxlength):
    """Fingerprint a file by calling the fpcalc application."""
    fpcalc = os.environ.get(FPCALC_ENVVAR, FPCALC_COMMAND)
    command = [fpcalc, "-length", str(maxlength), path]
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = proc.communicate()
    except OSError as exc:
        if exc.errno == errno.ENOENT:
            raise NoBackendError("fpcalc not found")
        else:
            raise FingerprintGenerationError("fpcalc invocation failed: %s: %s" %
                                             (str(exc), error))
    except UnicodeEncodeError:
        # Due to a bug in Python 2's subprocess on Windows, Unicode
        # filenames can fail to encode on that platform. See:
        # http://bugs.python.org/issue1759845
        raise FingerprintGenerationError("argument encoding failed")
    retcode = proc.poll()
    if retcode:
        raise FingerprintGenerationError("fpcalc exited with status %i: %s" %
                                         (retcode, error))

    duration = fp = None
    for line in output.splitlines():
        try:
            parts = line.split(b'=', 1)
        except ValueError:
            raise FingerprintGenerationError("malformed fpcalc output")
        if parts[0] == b'DURATION':
            try:
                duration = float(parts[1])
            except ValueError:
                raise FingerprintGenerationError("fpcalc duration not numeric")
        elif parts[0] == b'FINGERPRINT':
            fp = parts[1]

    if duration is None or fp is None:
        raise FingerprintGenerationError("missing fpcalc output")
    return duration, fp
