# TAGS

Package used for processing TAGS documents downloaded as tab-separated files.


## Setting up a document

```python
tags = TAGS.Document(path="./datasets/downloaded_tags_document.tsv")
```

## Properties and methods

### 1. All IDs

A TAGS.Document object has a property that contains a list of all IDs in the file for easy processing:

```python
tags.ids
```

# 2. Get data for a specific document

A TAGS.Document object can also get data through looking for a specific ID: (if no data, returns None)

```python
test_id = 1156639282024464385

tags.get_data_for_id(test_id) # get all data for an ID
tags.get_data_for_id(test_id, 'text') # get specific data for an ID
```