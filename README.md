
The archive_reader.py script (or the `ArchiveReader` class within) reads in your Mastodon archive outbox.json (specifically posts you made) and creates a `main.db` sqlite3 database.

The database holds two tables and one view: 

* `search_data`. This is a virtual table created with FTS5 that allows for full text search of your posts.
* `full_data`. This is every column from the archive that contains an `object_id`.
* `combined`. This is a view that combines the two tables above on extracted `int_id` column.

Creating the sqlite database requires pandas and [html2text](https://pypi.org/project/html2text/).

I also include a [Plotly Dash](https://dash.plotly.com) `app.py` to allow for GUI searching of the archive, using sqlite full text search ([FTS5](https://www.sqlite.org/fts5.html)) on the contents of the archived posts. You will need Plotly Dash installed to run this. It's not intended for deployment, but to run locally as a way to explore the database you created.

Usage

```bash

$ python archive_reader.py archive_folder_name 

```

That will create the sqlite database `main.db`.

Running app.py

```
python app.py
```

will launch a simple plotly dash app to search your archive.

<img width="1408" alt="Screenshot of the plotly Dash app in use returning some search results." src="https://user-images.githubusercontent.com/13702392/221355745-ece59b4a-399c-4262-bdd0-c97bd44f5102.png">


### TODO

* Figure out the list of dictionaries in the `attachments` portion of the JSON file and embed media attachments in the Dash app.
