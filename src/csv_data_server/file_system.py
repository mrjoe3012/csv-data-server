from __future__ import annotations
from typing import Any, Optional
from csv_data_server.config import get_config
from pathlib import Path
import os

CONFIG = get_config()

class FileSystem:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._root_dir = CONFIG.root_dir
        if not os.path.exists(self._root_dir):
            os.makedirs(self._root_dir)

    def _get_file(self, filename: str, headers: Optional[list[str]] = None):
        file_path = Path(os.path.join(self._root_dir, filename)).resolve()
        dir = Path(self._root_dir).resolve()
        try:
            file_path.relative_to(dir)
        except ValueError:
            raise RuntimeError("Invalid filename provided.")
        if not file_path.exists():
            with open(str(file_path), 'w') as f:
                if headers is not None:
                    f.write(','.join(headers) + '\n')
        return os.path.abspath(str(file_path))

    def add_rows(self, filename: str, rows: list[list[Any]],
                 headers: Optional[list[str]] = None) -> None:
        """
        :param filenanme: The file to fetch. 
        :param rows: The rows to add.
        """
        fp = self._get_file(filename, headers=headers)
        with open(fp, 'a') as f:
            for row in rows:
                f.write(
                    ','.join(map(str, row)) + '\n'
                )

    def get_file(self, filename: str) -> str:
        """
        :returns: Full path to the file in question.
        """
        return self._get_file(filename)

    def ls(self) -> list[str]:
        """
        :returns: List of all files.
        """
        files = os.listdir(self._root_dir)
        return files
