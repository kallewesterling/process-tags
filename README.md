# TAGS

Package used for processing [TAGS](https://tags.hawksey.info/) documents downloaded as tab-separated files.


## Setting up a simple document

```python
tags = TAGS.Document(path="./datasets/downloaded_tags_document.tsv")
```

## Setting up a TAGS DocumentSet

If you need to ingest more than one file or perhaps one or more directories into one dataset, you can do so using the `DocumentSet` object.

If you would only like to include a list of documents, you can do so by using the `paths` parameter:

```python
tags = TAGS.DocumentSet(paths=["./datasets/downloaded_tags_document.tsv", "./datasets/another_downloaded_tags_document.tsv"])
```

If you woud rather want to include any number of directories, you can do so using the `directories` parameter:

```python
tags = TAGS.DocumentSet(directories=["./datasets/", "./another_dataset_folder/"])
```

*Note that if you are including directories, make sure that there are no other .tsv files in the directories added. If there are, the script will likely crash.*

## Properties and methods

### 1. All IDs

Both the `TAGS.Document` and the `TAGS.DocumentSet` objects have a property that contains a list of all IDs in the file/s in the object for easy processing:

```python
tags.ids
```

### 2. Get data for a specific document

A `TAGS.Document` object can also retrieve data for a specific ID from the file using the `get_data_for_id` method: (if no data, returns `None`)

```python
test_id = 1156639282024464385

tags.get_data_for_id(test_id) # get all data for an ID
tags.get_data_for_id(test_id, 'text') # get specific data for an ID
```

Unfortunately, the TAGS.DocumentSet does not currently include such a method.
