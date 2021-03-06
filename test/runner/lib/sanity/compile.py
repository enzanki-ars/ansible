"""Sanity test for proper python syntax."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from lib.sanity import (
    SanityMultipleVersion,
    SanityMessage,
    SanityFailure,
    SanitySuccess,
    SanitySkipped,
)

from lib.util import (
    SubprocessError,
    display,
    find_python,
    parse_to_list_of_dict,
    ANSIBLE_ROOT,
)

from lib.util_common import (
    run_command,
)

from lib.config import (
    SanityConfig,
)


class CompileTest(SanityMultipleVersion):
    """Sanity test for proper python syntax."""
    def test(self, args, targets, python_version):
        """
        :type args: SanityConfig
        :type targets: SanityTargets
        :type python_version: str
        :rtype: TestResult
        """
        settings = self.load_settings(args, None, python_version)

        paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' or i.path.startswith('bin/'))
        paths = settings.filter_skipped_paths(paths)

        if not paths:
            return SanitySkipped(self.name, python_version=python_version)

        cmd = [find_python(python_version), os.path.join(ANSIBLE_ROOT, 'test/sanity/compile/compile.py')]

        data = '\n'.join(paths)

        display.info(data, verbosity=4)

        try:
            stdout, stderr = run_command(args, cmd, data=data, capture=True)
            status = 0
        except SubprocessError as ex:
            stdout = ex.stdout
            stderr = ex.stderr
            status = ex.status

        if stderr:
            raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

        if args.explain:
            return SanitySuccess(self.name, python_version=python_version)

        pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<message>.*)$'

        results = parse_to_list_of_dict(pattern, stdout)

        results = [SanityMessage(
            message=r['message'],
            path=r['path'].replace('./', ''),
            line=int(r['line']),
            column=int(r['column']),
        ) for r in results]

        results = settings.process_errors(results, paths)

        if results:
            return SanityFailure(self.name, messages=results, python_version=python_version)

        return SanitySuccess(self.name, python_version=python_version)
