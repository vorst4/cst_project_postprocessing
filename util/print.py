import os
import subprocess
from datetime import datetime

# os.name = nt: Windows OR posix: Linux
is_running_on_desktop = os.name == 'nt'


class Print:
    print_log = True

    def __init__(
            self,
            path_log: str,
            job_id: int,
            n_jobs: int,
            partition_id: int
    ):
        self.path_log = path_log

        # make sure file exists
        print(self.path_log)
        with open(self.path_log, 'w') as file:
            file.write('')

        # write system info
        self.log(system_info(job_id, n_jobs, partition_id))

    @staticmethod
    def _timestamp():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + ' |   '

    @staticmethod
    def _indent():
        return ' ' * 23 + ' |   '

    def log(self, msg):
        # print log to console
        if self.print_log:
            print(msg)

        # append message to log
        with open(self.path_log, 'a') as file:

            # split msg at linebreaks
            for idx, line in enumerate(str(msg).splitlines()):

                # write either a timestamp or indent
                if idx == 0:
                    file.write(self._timestamp())
                else:
                    file.write(self._indent())

                # write the line
                file.write(line + '\n')


def system_info(
            job_id: int,
            n_jobs: int,
        partition_id: int
) -> str:
    info = 'job_id = %i\n' % job_id
    info += 'n_jobs = %i\n' % n_jobs
    info += 'partition_id = %i\n' % partition_id
    if not is_running_on_desktop:
        info += "cpu info:\n"
        info += subprocess.check_output('lscpu', shell=True).decode('utf-8')
        info += '\n'
        info += "memory info:\n"
        info += subprocess.check_output('free -h', shell=True).decode('utf-8')
        info += '\n'
    return info
