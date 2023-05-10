import os
import shutil
from threading import Timer


def delete_all_in_folder_with_delay(folder, delay=2.0):
    Timer(delay, delete_all_in_folder, [folder]).start()


def delete_all_in_folder(folder):
    for root, dirs, files in os.walk(folder):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(root, d)


def delete_file_with_delay(filename, delay=2.0):
    Timer(delay, delete_file, [filename]).start()


def delete_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def print_array_nicely(array):
    result_string = ''
    for index, item in enumerate(array, start=1):
        result_string += '{}: {}\n'.format(index, item)
    return result_string
