
import subprocess
import os


def get_version():
    return (
        subprocess
        .run(["poetry", "version", "-s"], capture_output=True, text=True)
        .stdout
        .rstrip())


def get_lily_path():
    return os.path.join(os.getcwd(), '.lily')


def get_project_path():
    return os.getcwd()
