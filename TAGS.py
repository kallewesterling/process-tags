import csv
from pathlib import Path


class Document():

    def __init__(self, path, suppress_warnings=False):
        self.path = Path(path)
        self.suppress_warnings = suppress_warnings
        self._all_ids = None


    @property
    def ids(self):
        if self._all_ids is None: self._all_ids = self.get_ids()
        return(self._all_ids)


    def __len__(self):
        if self._all_ids is None: self._all_ids = self.get_ids()
        return(len(self._all_ids))


    def get_ids(self):
        if not Path(self.path).is_file(): raise RuntimeError(f"File {self.path} does not exist.")

        all_ids = []
        with Path(self.path).open("r") as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, rows in enumerate(reader):
                if not rows['created_at'] and not rows['from_user'] and not rows['text']: pass # skip empty rows
                try:
                    id_int = int(rows['id_str'])
                    all_ids.append(id_int)
                except:
                    if not self.suppress_warnings: print(f"Warning: ID ({rows['id_str']}) could not be interpreted as number.")
        return(list(set(all_ids)))


    def get_data_for_id(self, _id, key = None):
        with open(self.path) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for rows in reader:
                if str(rows['id_str']) == str(_id):
                    if key is None: return(rows)
                    else: return(rows.get(key, None))
        return(None)


class DocumentSet():

    def __init__(self, documents=[], directories=[], suppress_warnings=False):

      # Ingest and strip [documents] and [directories] from non-existent entities as well as those that are not documents/directories
      self.documents = [Path(x) for x in documents if Path(x).exists() and Path(x).is_file()]
      self._error_documents = [Path(x) for x in documents if not Path(x).exists() or not Path(x).is_file()]

      self.directories = [Path(x) for x in directories if Path(x).exists() and Path(x).is_dir()]
      self._error_directories = [Path(x) for x in directories if not Path(x).exists() or not Path(x).is_dir()]

      self.suppress_warnings = suppress_warnings

      if not self.suppress_warnings:
        if len(self._error_documents):
          print("An error occurred while attempting to ingest the following documents:")
          for d in self._error_documents: print(f" - {d}")
        elif len(self._error_directories):
          print("An error occurred while attempting to ingest the following directories:")
          for d in self._error_directories: print(f" - {d}")

      # Set up placeholders
      self._documents_dict = {}

      # Process all of the self.documents Paths
      for doc_path in self.documents:
        if doc_path not in self._documents_dict: self._documents_dict[doc_path] = Document(doc_path, suppress_warnings=self.suppress_warnings)

      # Process all of the self.directories Paths
      for directory in self.directories:
        if not directory.exists() or not directory.is_dir(): raise RuntimeError(f"Directory {directory} does not exist or is not a directory.")
        for doc_path in directory.glob("*.tsv"):
          if doc_path not in self._documents_dict:
            self._documents_dict[doc_path] = Document(doc_path, suppress_warnings=self.suppress_warnings)
          elif doc_path in self._documents_dict and not suppress_warnings:
            print(f"File {doc_path} was already ingested.")

      self.ids = []
      for path, doc in self._documents_dict.items():
        self.ids.extend(doc.ids)

      self.ids = list(set(self.ids))

    def __len__(self):
        return(len(self.ids))