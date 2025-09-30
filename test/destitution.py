import sys
import os
import pprint
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from csv_text_search import TextSearcher
import unittest


class DestitutionFr(unittest.TestCase):
    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        self.searcher = TextSearcher(
            dataset_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\complete_data_ENG_FRE.csv",  # dataset file path
            queries_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\At the margins\queries_simple.csv",
            law_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\THE_LAW\THE_LAW_sections.csv", # path to the Law
        )

    def test_destitution(self):
        results = self.searcher.search_text(query_word='destitution', language_filter='FRE')
        pprint.pprint(results)
        print(f"Keys: \n {results[-1].keys()}")
        # Looks like the query word is mistakenly printed as the entire text
        self.assertGreater(len(results), 0)


if __name__ == '__main__':
    unittest.main()
