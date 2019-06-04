from collections import OrderedDict
import os
import sys
import subprocess
import zipfile


__all__ = ["BuildPlan", "BuildProducts"]


class BuildPlan:
    def __init__(self, script):
        self.script = script
        self.files  = OrderedDict()

    def add_file(self, filename, content):
        assert isinstance(filename, str) and filename not in self.files
        # Just to make sure we don't accidentally overwrite anything.
        assert not os.path.normpath(filename).startswith("..")
        self.files[filename] = content

    def execute(self, root="build", run_script=True):
        os.makedirs(root, exist_ok=True)
        cwd = os.getcwd()
        try:
            os.chdir(root)

            for filename, content in self.files.items():
                dirname = os.path.dirname(filename)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)

                mode = "wt" if isinstance(content, str) else "wb"
                with open(filename, mode) as f:
                    f.write(content)

            if run_script:
                if sys.platform.startswith("win32"):
                    subprocess.run(["cmd", "/c", "{}.bat".format(self.script)], check=True)
                else:
                    subprocess.run(["sh", "{}.sh".format(self.script)], check=True)

                return BuildProducts(os.getcwd())

        finally:
            os.chdir(cwd)

    def archive(self, file):
        with zipfile.ZipFile(file, "w") as archive:
            # Write archive members in deterministic order and with deterministic timestamp.
            for filename in sorted(self.files):
                archive.writestr(zipfile.ZipInfo(filename), self.files[filename])


class BuildProducts:
    def __init__(self, root):
        self._root = root

    def get(self, filename, mode="b"):
        assert mode in "bt"
        with open(os.path.join(self._root, filename), "r" + mode) as f:
            return f.read()
