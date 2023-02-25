import sqlite3
import json
import pandas as pd
from html2text import html2text, HTML2Text
from urllib.parse import urlparse
import argparse


class ArchiveReader():

    def __init__(self, dir_name) -> None:
        with open(f'{dir_name}/outbox.json', 'r') as f:
            myjson = json.load(f)
            self.df = pd.json_normalize(
                myjson['orderedItems'],
                sep='_').dropna(subset=['object_content', 'object_id'])
        print("Loaded JSON")
        self.text_maker = HTML2Text()
        self.text_maker.ignore_links = True
        self.text_maker.bypass_tables = False
        self.process_df()
        print("JSON processed to Dataframe")

    def clean_text(self, html):
        clean_text = self.text_maker.handle(html)
        clean_text = clean_text.replace('\n', ' ').strip()
        return clean_text

    @staticmethod
    def get_id(url):
        return int(urlparse(url).path.rpartition('/')[-1])

    def process_df(self):
        self.df['markdown_content'] = self.df['object_content'].map(
            html2text, na_action='ignore')
        self.df['text_content'] = self.df['object_content'].map(
            self.clean_text, na_action='ignore')
        self.df['int_id'] = self.df['object_id'].map(self.get_id,
                                                     na_action='ignore')

    def save_to_sql(self):
        print("Creating table")
        with sqlite3.connect('main.db') as con:
            con.execute("DROP TABLE IF EXISTS search_data;")
            con.execute(
                "CREATE VIRTUAL TABLE search_data USING fts5(text_content,int_id, tokenize = 'porter ascii');"
            )
        print("Loading data to table")
        self.df[['text_content', 'int_id']].to_sql('search_data',
                                                   con=con,
                                                   if_exists='append',
                                                   index=False)
        self.df.drop(columns=[
            'text_content', 'to', 'cc', 'object_to', 'object_cc', '@context',
            'object_attachment', 'object_tag', 'object_replies_first_items'
        ]).to_sql('full_data', con=con, if_exists='replace', index=False)
        with sqlite3.connect('main.db') as con:
            con.execute(
                "CREATE INDEX IF NOT EXISTS full_data_post_id on full_data(int_id);"
            )
            con.execute(
                'CREATE VIEW IF NOT EXISTS combined as select text_content,fd.* from search_data sd left join full_data fd on fd.int_id = sd.int_id;'
            )
        print("Success")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder_name', type=str)

    args = parser.parse_args()

    a = ArchiveReader(args.folder_name)
    a.save_to_sql()
