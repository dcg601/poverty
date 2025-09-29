import pandas as pd
import re
from typing import List, Dict, Tuple
import sys

# Some constants
FULLTEXT = 'THE_LAW'
LANGUAGE = 'languageisocode'

class TextSearcher:
    def __init__(self, dataset_path: str, law_path:str, queries_path: str, rows: int=None):
        """
        Initialize the TextSearcher with dataset and queries CSV files.
        
        Args:
            dataset_path: Path to CSV file with columns: itemid, language, fulltext
            law_path: Path to CSV file with only 'THE LAW' sections. The file contains judgments after 2000, with some omissions
            queries_path: Path to CSV file with English and French query words
        """
        self._columns = ['itemid','appno', 'docname', 'doctype', 'languageisocode', 'article', 'violation', 'year', 'THE_LAW']
        # read the full dataset but with less columns to save loading time
        self.df_all = pd.read_csv(dataset_path, usecols=self._columns[:-1], low_memory=False)
        self.law = pd.read_csv(law_path, nrows=rows) 
        self.queries = pd.read_csv(queries_path)
    
        self.df_all.columns = self.df_all.columns.str.strip()
        self.law.columns = self.law.columns.str.strip()

        # Merge the full dataset with the dataset with the law sections, to filter out cases where the law section is missing
        merged = self.df_all.merge(self.law, how='left', on='itemid')
        # print(merged.head())
        # missing_in_df_all = set(self.law['itemid']) - set(self.df_all['itemid'])
        # print(f"Itemids in law but not in df_all: {list(missing_in_df_all)[:10]} (showing up to 10)", flush=True)
        # Filter out cases where we are missing the full dataset
        self.dataset = merged.loc[~pd.isna(merged['THE_LAW'])]

        # Clean column names (remove whitespace)
        self.dataset.columns = self.dataset.columns.str.strip()
        self.queries.columns = self.queries.columns.str.strip()
        
        print(f"Loaded dataset after merging and removing nulls with {len(self.dataset)} rows")
        print(f"Dataset columns: {list(self.dataset.columns)}")
        print(f"Loaded queries with {len(self.queries)} rows")
        print(f"Query columns: {list(self.queries.columns)}")
    
    def get_context(self, text: str, query: str, context_words: int = 10) -> str:
        """
        Extract context around the found query term.
        
        Args:
            text: The full text where the query was found
            query: The search term
            context_words: Number of words to include before and after the match
        
        Returns:
            Context string with the query term highlighted
        """
        # Case-insensitive search with word boundaries
        pattern = r'\b' + re.escape(query.lower()) + r'\b'
        text_lower = text.lower()
        
        matches = list(re.finditer(pattern, text_lower))
        if not matches:
            return ""
        
        contexts = []
        words = text.split()
        
        for match in matches:
            # Find the word position in the original text
            char_pos = match.start()
            word_pos = len(text[:char_pos].split()) - 1
            word_pos = max(0, word_pos)
            
            # Extract context
            start_idx = max(0, word_pos - context_words)
            end_idx = min(len(words), word_pos + context_words + 1)
            
            context_words_list = words[start_idx:end_idx]
            
            # Highlight the matching word(s)
            highlighted_context = []
            for i, word in enumerate(context_words_list):
                if re.search(pattern, word.lower()):
                    highlighted_context.append(f"**{word}**")
                else:
                    highlighted_context.append(word)
            
            context = " ".join(highlighted_context)
            if start_idx > 0:
                context = "..." + context
            if end_idx < len(words):
                context = context + "..."
            
            contexts.append(context)
        
        return " | ".join(contexts)  # Join multiple contexts with separator
    
    def search_text(self, query_word: str, language_filter: str = None, context_words: int = 10) -> List[Dict]:
        """
        Search for a query word in the dataset.
        
        Args:
            query_word: The word to search for
            language_filter: Optional language filter ('english', 'french', etc.)
        
        Returns:
            List of dictionaries containing search results
        """
        results = []
        
        # Filter by language if specified
        search_data = self.dataset.copy()
        if language_filter:
            search_data = search_data[search_data[LANGUAGE].str.lower() == language_filter.lower()]
        
        # Search in fulltext column
        pattern = r'\b' + re.escape(query_word.lower()) + r'\b'
        
        for idx, row in search_data.iterrows():
            if pd.isna(row[FULLTEXT]):
                continue
                
            fulltext = str(row[FULLTEXT])
            if re.search(pattern, fulltext.lower()):
                context = self.get_context(fulltext, query_word, context_words)
                
                result = {
                    'itemid': row['itemid'],
                    'language': row[LANGUAGE],
                    'query_word': query_word,
                    'context': context,
                    FULLTEXT: fulltext
                }
                results.append(result)
        
        return results
    
    def search_all_queries(self, context_words: int = 10) -> pd.DataFrame:
        """
        Search for all query words from the queries table.
        
        Args:
            context_words: Number of context words to include around matches
        
        Returns:
            DataFrame with all search results
        """
        all_results = []
        
        # Assume the queries CSV has columns for English and French
        # Adjust these column names based on your actual CSV structure
        query_columns = [col for col in self.queries.columns if col.lower() in ['english', 'french', 'en', 'fr']]
        
        if not query_columns:
            # If no standard language columns found, use all columns
            query_columns = self.queries.columns.tolist()
        
        print(f"Searching using columns: {query_columns}")
        
        for _, query_row in self.queries.iterrows():
            for col in query_columns:
                if pd.isna(query_row[col]):
                    continue
                
                query_word = str(query_row[col]).strip()
                if not query_word:
                    continue
                
                # Determine language preference for filtering (optional)
                language_filter = None
                if col.lower() in ['english', 'en']:
                    language_filter = 'eng'
                elif col.lower() in ['french', 'fr']:
                    language_filter = 'fre'
                
                # Search for this query word
                results = self.search_text(query_word, language_filter, context_words)
                
                for result in results:
                    result['query_language'] = col
                    all_results.append(result)
        
        if not all_results:
            print("No matches found!")
            return pd.DataFrame()
        
        # Convert to DataFrame
        results_df = pd.DataFrame(all_results)
        
        # Group by itemid and query_word to concatenate multiple contexts
        grouped_results = []
        
        sys.stderr.write(f"Results from {query_word} have returned with lenght:{results_df.shape[0]} rows and columns {results_df.columns}")
        for (itemid, query_word), group in results_df.groupby(['itemid', 'query_word']):
            # Concatenate contexts
            contexts = group['context'].tolist()
            combined_context = " | ".join([ctx for ctx in contexts if ctx])
            
            grouped_result = {
                'itemid': itemid,
                'language': group.iloc[0]['language'],
                'query_word': query_word,
                'query_language': group.iloc[0]['query_language'],
                'combined_context': combined_context,
                'match_count': len(group),
                FULLTEXT: group.iloc[0][FULLTEXT]
            }
            grouped_results.append(grouped_result)
        
        return pd.DataFrame(grouped_results)
    
    def save_results(self, results_df: pd.DataFrame, output_path: str = "search_results.csv"):
        """Save results to CSV file."""
        if not results_df.empty:
            # Select columns for output (excluding fulltext to keep file manageable)
            output_columns = ['itemid', 'language', 'query_word', 'query_language', 
                            'combined_context', 'match_count']
            
            output_df = results_df[output_columns].copy()
            output_df.to_csv(output_path, index=False, encoding='utf-8')
            print(f"Results saved to {output_path}")
        else:
            print("No results to save.")

# Example usage
if __name__ == "__main__":
    OUTPATH = r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\At the margins\\"
    # Initialize the searcher
    searcher = TextSearcher( # Use "C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\THE_LAW\THE_LAW_sections.csv" and join with the other to get the complete dataset
        # Check also if the two datasets have the same timespan
        #   The law is after 2000
        dataset_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\complete_data_ENG_FRE.csv",  # dataset file path
        law_path=r"C:\Users\dcg601\OneDrive - University of Copenhagen\iCourts Projects\ECtHR\DATA\THE_LAW\THE_LAW_sections.csv", # path to the Law
        queries_path=rf"{OUTPATH}queries_simple.csv"   # queries file path
        #rows=5000
    )
    
    # Search all queries
    results = searcher.search_all_queries(context_words=20)
    
    if not results.empty:
        # Display results
        print(f"\nFound {len(results)} unique matches:")
        print("="*80)
        
        for _, row in results.iterrows():
            print(f"Item ID: {row['itemid']}")
            print(f"Language: {row['language']}")
            print(f"Query: '{row['query_word']}' ({row['query_language']})")
            print(f"Matches: {row['match_count']}")
            print(f"Context: {row['combined_context']}")
            print("-" * 80)
        
        # Save to CSV
        print("Saving to %s" %rf"{OUTPATH}search_results.csv")
        searcher.save_results(results, rf"{OUTPATH}search_results.csv")
        
        # Optional: Display summary statistics
        print(f"\nSummary:")
        print(f"Total unique matches: {len(results)}")
        print(f"Items with matches: {results['itemid'].nunique()}")
        print(f"Languages found: {results['language'].unique()}")
        print(f"Query words that found matches: {results['query_word'].nunique()}")

        # TODO: destitution is the same for English and French and the script seems to search French but says the result was found after searching English 
    
    # ---- EXAMPLE USE ----
    # # Example of searching for a specific word
    # print("\n" + "="*80)
    # print("Example: Searching for specific word 'example'")
    # specific_results = searcher.search_text("example")
    
    # for result in specific_results:
    #     print(f"Found in item {result['itemid']}: {result['context']}")
