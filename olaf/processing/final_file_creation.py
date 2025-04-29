from pathlib import Path

from olaf.utils.data_handler import DataHandler


class FinalFileCreation:
    def __init__(self, project_folder: Path, includes, excludes) -> None:
        """ """
        self.project_folder = project_folder
        self.files_per_date = self._get_files_per_date(includes, excludes)

    def _get_files_per_date(self, includes, excludes):
        """
        Get all the files in the project folder and group them by date.
        """
        file_paths = []
        # Go through every folder in the project folder and create a data_handler object for it
        for folder in self.project_folder.iterdir():
            if folder.is_dir():
                data_handler = DataHandler(folder, 0, includes=includes, excludes=excludes)
                file_paths.append(data_handler.data_file)

        files_per_date = {}
        for file in self.project_folder.iterdir():
            if file.is_file() and file.suffix == ".csv":
                date = file.name.split("_")[0]
                if date not in files_per_date:
                    files_per_date[date] = []
                files_per_date[date].append(file)
        return files_per_date
