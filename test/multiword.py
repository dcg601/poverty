import sys
import os
import pprint
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from csv_text_search import TextSearcher, FULLTEXT
import unittest

class MultiWordTest(unittest.TestCase):
        def __init__(self, methodName = "runTest"):
            super().__init__(methodName)
            print(f"Initializing MultiWordTest", flush=True)
            self.searcher = TextSearcher(
                dataset_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\complete_data_ENG_FRE.csv",  # dataset file path
                queries_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\At the margins\queries_simple_v2.csv",
                law_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\THE_LAW\THE_LAW_sections.csv", # path to the Law
            )

        def test_subsistance(self):
              query = '(moyens de)? subsistance'
            #   query = 'subsistance'
              print(f"Will query with {query}", flush=True)
              text = str(self.searcher.dataset[FULLTEXT])
              context = self.searcher.search_text(query_word=query, language_filter='FRE')
              pprint.pprint(context[0]['combined_context'])
            #   self.assertGreater(len(context), 0)


if __name__ == '__main__':
      unittest.main()