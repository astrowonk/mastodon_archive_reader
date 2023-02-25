
This app reads in the `main.db` sqlite3 database created by the archive_reader.py script (or the `ArchiveReader` class within), and presents a very simple GUI search interface to full text search the database.

`ArchiveReader` creates two tables and one view: 

    * `search_data`. This is a virtual table created with FTS5 that allows for full text search of your posts.
    * `full_data`. This is every column from the archive that contains an `object_id` 
    * `combined`. This is a view that combines the two tables above on extracted integer post id column

