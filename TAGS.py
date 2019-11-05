import csv
from pathlib import Path


class Document():

    def __init__(self, path, suppress_warnings=False):
        self.path = Path(path)
        self.suppress_warnings = suppress_warnings
        self._all_ids = None


    @property
    def ids(self):
        if self._all_ids is None:
            self._all_ids = self.get_ids()
        return(self._all_ids)


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

    def __init__(self):