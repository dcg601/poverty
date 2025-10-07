import sys
import os
import pprint
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from csv_text_search import TextSearcher
import unittest


class RegexQuery(unittest.TestCase):
    def __init__(self, methodName = "runTest"):
        super().__init__(methodName)
        self.searcher = TextSearcher(
            dataset_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\complete_data_ENG_FRE.csv",  # dataset file path
            queries_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\At the margins\queries_simple_v2.csv",
            law_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\THE_LAW\THE_LAW_sections.csv", # path to the Law
        )    
    
    def test_complex_query(self):
        result = self.searcher.search_text(query_word='(moyens de)? subsistance', language_filter='FRE')
        self.assertEqual(len(result), 159)

    def test_complex_query2(self):
        result = self.searcher.search_text(query_word="(plonger dans)? la gêne", language_filter='FRE')
        self.assertEqual(len(result), 12)

if __name__ == '__main__':
    unittest.main()