import os 


class Basics:
    def __init__(self):
        # self.getcwd = os.getcwd()
        self.getcwd = os.path.abspath(__file__)
        self.dotcsv = ".csv"

    def Get_path_files(self, subfolder1, subfolder2):
        path_folder = self.getcwd.split("src")[0] + f"data/inputs/{subfolder1}/{subfolder2}_"
        path_files = [(path_folder + f"{i}" + self.dotcsv) for i in range(1, 366)]
        return path_files