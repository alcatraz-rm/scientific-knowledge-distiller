import os


def find_root_directory():
    initial_wd = os.getcwd()
    while os.path.split(os.getcwd())[-1] != 'scientific-knowledge-distiller':
        os.chdir(os.path.join(os.getcwd(), '..'))
    root_path = os.getcwd()
    os.chdir(initial_wd)

    return root_path

