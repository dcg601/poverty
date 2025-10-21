import streamlit as st
import pandas as pd
import re
from pathlib import Path

# Configure the page
st.set_page_config(page_title="CSV Law Text Search", layout="wide")

# Constants
EXPECTED_COLUMNS = ['itemid', 'appno', 'docname', 'language', 'article', 'violation', 'year', 
                   'query_word', 'link', 'query_language', 'context', 'match_count', 'THE_LAW']

@st.cache_data
def load_csv_file(file_path):
    """Load the CSV file and return as DataFrame"""
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        df.columns = df.columns.str.strip()
        return df, None
    except Exception as e:
        return None, str(e)

def filter_by_text(df, column_name, search_term, use_regex=False):
    """Filter dataframe by text in specified column"""
    if not search_term or search_term.strip() == "":
        return df
    
    if column_name not in df.columns:
        return df
    
    try:
        if use_regex:
            # Use regex search with word boundaries for plain text
            pattern = r'\b' + re.escape(search_term.lower()) + r'\b'
            mask = df[column_name].astype(str).str.contains(pattern, case=False, na=False, regex=True)
        else:
            # Simple substring search
            mask = df[column_name].astype(str).str.contains(search_term, case=False, na=False, regex=False)
        return df[mask]
    except Exception as e:
        st.error(f"Error filtering by {column_name}: {str(e)}")
        return df

def filter_by_language(df, language):
    """Filter dataframe by language"""
    if language == "All":
        return df
    
    language_map = {
        "English": "eng",
        "French": "fre"
    }
    
    lang_code = language_map.get(language, language.lower())
    
    if 'language' in df.columns:
        return df[df['language'].astype(str).str.lower() == lang_code]
    elif 'languageisocode' in df.columns:
        return df[df['languageisocode'].astype(str).str.lower() == lang_code]
    else:
        st.warning("No language column found in dataset")
        return df

def filter_by_year(df, year_input):
    """Filter dataframe by year"""
    if not year_input or year_input.strip() == "":
        return df
    
    if 'year' not in df.columns:
        return df
    
    try:
        # Support both exact year and year ranges
        if '-' in year_input:
            # Year range (e.g., "2010-2015")
            start, end = year_input.split('-')
            start_year = int(start.strip())
            end_year = int(end.strip())
            mask = (df['year'].astype(float) >= start_year) & (df['year'].astype(float) <= end_year)
            return df[mask]
        else:
            # Exact year or partial match
            mask = df['year'].astype(str).str.contains(year_input.strip(), na=False)
            return df[mask]
    except Exception as e:
        st.error(f"Error filtering by year: {str(e)}")
        return df

def paginate_dataframe(df, page_size, page_num):
    """Paginate the dataframe"""
    start_idx = page_num * page_size
    end_idx = start_idx + page_size
    return df.iloc[start_idx:end_idx]

def _preprocess_appno(appno) -> str:
    # short hack to display only the first casenos if there are more than one assigned
    appnos = appno.split(';')
    appnos_str = f"{';'.join(appnos[:3])} and others" if len(appnos) > 3 else ';'.join(appnos)

    return appnos_str

def display_result_accordion(row, idx):
    """Display a single result in an accordion/expander"""
    # Create a meaningful title
    title_parts = []
    
    if 'appno' in row and pd.notna(row['appno']):
        appnos_str = _preprocess_appno(row['appno'])
        title_parts.append(f"Case {appnos_str}")
    
    if 'year' in row and pd.notna(row['year']):
        title_parts.append(f"- Year: ({row['year']})")
    
    if 'query_word' in row and pd.notna(row['query_word']):
        title_parts.append(f"- Query: '{row['query_word']}'")
    
    # Use itemid for unique identification if available
    record_id = row['itemid'] if 'itemid' in row and pd.notna(row['itemid']) else idx + 1
    title = " ".join(title_parts) if title_parts else f"Record {record_id}"
    
    with st.expander(f"📄 {title}"):
        # Display metadata in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'itemid' in row and pd.notna(row['itemid']):
                st.markdown(f"**Item ID:** {row['itemid']}")
            if 'appno' in row and pd.notna(row['appno']):
                appnos_str = _preprocess_appno(row['appno'])               
                st.markdown(f"**Application No:** {appnos_str}")
            if 'year' in row and pd.notna(row['year']):
                st.markdown(f"**Year:** {row['year']}")
        
        with col2:
            if 'language' in row and pd.notna(row['language']):
                lang_display = {"eng": "English", "fre": "French"}.get(row['language'], row['language'])
                st.markdown(f"**Language:** {lang_display}")
            if 'article' in row and pd.notna(row['article']):
                st.markdown(f"**Article:** {row['article']}")
            if 'violation' in row and pd.notna(row['violation']):
                st.markdown(f"**Violation:** {row['violation']}")
        
        with col3:
            if 'query_word' in row and pd.notna(row['query_word']):
                st.markdown(f"**Query Word:** {row['query_word']}")
            if 'query_language' in row and pd.notna(row['query_language']):
                st.markdown(f"**Query Language:** {row['query_language']}")
            if 'match_count' in row and pd.notna(row['match_count']):
                st.markdown(f"**Match Count:** {row['match_count']}")
        
        # Display link if available
        if 'link' in row and pd.notna(row['link']):
            st.markdown(f"🔗 [View on HUDOC]({row['link']})")
        
        st.markdown("---")
        
        # Display context if available
        if 'context' in row and pd.notna(row['context']):
            st.markdown("**Context:**")
            st.markdown(row['context'])
            st.markdown("---")
        
        # Display THE_LAW text
        if 'THE_LAW' in row and pd.notna(row['THE_LAW']):
            st.markdown("**THE LAW Section:**")
            law_text = str(row['THE_LAW'])
            
            # Show preview (first 1000 characters)
            # Use itemid + query_word for the key to ensure uniqueness (same itemid can match multiple queries)
            itemid_part = row['itemid'] if 'itemid' in row and pd.notna(row['itemid']) else f"idx_{idx}"
            query_part = row['query_word'] if 'query_word' in row and pd.notna(row['query_word']) else ""
            # Create a unique key by combining itemid and query_word (sanitize query_word for key use)
            query_sanitized = str(query_part).replace(" ", "_").replace("'", "").replace('"', '')[:20]
            unique_key = f"{itemid_part}_{query_sanitized}" if query_part else str(itemid_part)
            
            if len(law_text) > 1000:
                st.write(law_text[:1000] + "... (continued)")
                with st.expander("Click to view full text"):
                    st.text_area("Full Text", law_text, height=300, key=f"law_text_{unique_key}")
            else:
                st.write(law_text)

def main():
    st.title("🔍 Poverty Search Application")
    st.markdown("Upload a CSV file with the poverty cases and search through 'THE LAW' sections")
    
    # File upload section
    st.sidebar.header("📁 Load Data")
    
    # Option 1: File uploader
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="Upload a CSV file with poverty related data"
    )
    
    # Option 2: Manual path input
    st.sidebar.markdown("**OR**")
    manual_path = st.sidebar.text_input(
        "Enter file path manually:",
        placeholder=r"C:\path\to\your\file.csv",
        help="Enter the full path to your CSV file"
    )
    
    # Load the data
    df = None
    data_source = None
    
    if uploaded_file is not None:
        df, error = load_csv_file(uploaded_file)
        data_source = uploaded_file.name
        if error:
            st.sidebar.error(f"Error loading file: {error}")
            return
    elif manual_path and manual_path.strip():
        if Path(manual_path).exists():
            df, error = load_csv_file(manual_path)
            data_source = manual_path
            if error:
                st.sidebar.error(f"Error loading file: {error}")
                return
        else:
            st.sidebar.error("File path does not exist!")
            return
    
    if df is None:
        st.info("👈 Please upload a CSV file or enter a file path in the sidebar to get started")
        
        # Show expected format
        with st.expander("ℹ️ Expected CSV Format"):
            st.markdown("The CSV file should contain the following columns:")
            for col in EXPECTED_COLUMNS:
                st.markdown(f"- `{col}`")
        
        return
    
    # Display data info
    st.sidebar.success(f"✅ Loaded {len(df):,} records")
    st.sidebar.info(f"📊 Source: {data_source}")
    
    # Display available columns
    with st.sidebar.expander("Available Columns"):
        st.write(df.columns.tolist())
    
    # Search interface
    st.markdown("---")
    st.subheader("🔎 Search Filters")
    
    # Create filter columns
    col1, col2 = st.columns(2)
    
    with col1:
        # THE_LAW text search
        law_search = st.text_input(
            "Search in THE_LAW (plain text):",
            placeholder="Enter text to search in legal documents...",
            help="Search for text in the THE_LAW column"
        )
        
        # Article search
        article_search = st.text_input(
            "Search in Article:",
            placeholder="Enter article number or text...",
            help="Search for specific article references"
        )
    
    with col2:
        # Context search
        context_search = st.text_input(
            "Search in Context:",
            placeholder="Enter text to search in context...",
            help="Search for text in the context column"
        )
        
        # Year search
        year_search = st.text_input(
            "Search by Year:",
            placeholder="e.g., 2020 or 2015-2020",
            help="Enter a specific year or year range (e.g., 2015-2020)"
        )
    
    # Add a third row for language filter
    language_filter = st.selectbox(
        "Filter by Language:",
        options=["All", "English", "French"],
        help="Filter results by document language",
        width=200
    )
    
    # Search button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        search_button = st.button("🔍 Apply Filters", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🔄 Clear Filters", use_container_width=True)
    
    # Initialize session state
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = df
        st.session_state.page_num = 0
    if 'page_size' not in st.session_state:
        st.session_state.page_size = 25
    
    if clear_button:
        st.session_state.filtered_df = df
        st.session_state.page_num = 0
        st.rerun()
    
    # Apply filters only when search button is clicked
    if search_button:
        filtered_df = df.copy()
        
        # Apply THE_LAW filter
        if law_search and 'THE_LAW' in filtered_df.columns:
            filtered_df = filter_by_text(filtered_df, 'THE_LAW', law_search, use_regex=True)
        
        # Apply article filter
        if article_search and 'article' in filtered_df.columns:
            filtered_df = filter_by_text(filtered_df, 'article', article_search, use_regex=False)
        
        # Apply context filter
        if context_search and 'context' in filtered_df.columns:
            filtered_df = filter_by_text(filtered_df, 'context', context_search, use_regex=True)
        
        # Apply year filter
        if year_search:
            filtered_df = filter_by_year(filtered_df, year_search)
        
        # Apply language filter
        if language_filter != "All":
            filtered_df = filter_by_language(filtered_df, language_filter)
        
        st.session_state.filtered_df = filtered_df
        st.session_state.page_num = 0
    
    results = st.session_state.filtered_df
    
    # Display results summary
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Results", f"{len(results):,}")
    with col2:
        st.metric("📁 Original Dataset", f"{len(df):,}")
    with col3:
        percentage = (len(results) / len(df) * 100) if len(df) > 0 else 0
        st.metric("📈 Match Rate", f"{percentage:.1f}%")
    
    if len(results) > 0:
        # Download results
        st.markdown("### 📥 Export Results")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = results.to_csv(index=False, encoding='utf-8').encode('utf-8')
            st.download_button(
                label="📄 Download All Results (CSV)",
                data=csv,
                file_name="filtered_search_results.csv",
                mime="text/csv",
                width='content'
            )
        
        with col2:
            # Download without THE_LAW column (smaller file)
            if 'THE_LAW' in results.columns:
                results_no_law = results.drop(columns=['THE_LAW'])
                csv_no_law = results_no_law.to_csv(index=False, encoding='utf-8').encode('utf-8')
                st.download_button(
                    label="📄 Download without THE_LAW (smaller)",
                    data=csv_no_law,
                    file_name="filtered_results_summary.csv",
                    mime="text/csv",
                    width='content'
                )
        
        # Pagination settings
        st.markdown("---")
        st.markdown("### 📋 Results Display")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            page_size = st.selectbox(
                "Results per page:",
                options=[5, 10, 25, 50, 100],
                index=[5, 10, 25, 50, 100].index(st.session_state.page_size),
                key="page_size_selector"
            )
            # Update session state if changed
            if page_size != st.session_state.page_size:
                st.session_state.page_size = page_size
                st.session_state.page_num = 0  # Reset to first page when page size changes
        
        # Calculate total pages
        total_pages = (len(results) - 1) // page_size + 1 if len(results) > 0 else 1
        
        # Pagination controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", key="first_page", disabled=st.session_state.page_num == 0, use_container_width=True):
                st.session_state.page_num = 0
                st.rerun()
        
        with col2:
            if st.button("◀️ Prev", key="prev_page", disabled=st.session_state.page_num == 0, use_container_width=True):
                st.session_state.page_num -= 1
                st.rerun()
        
        with col3:
            st.markdown(
                f"<div style='text-align: center; padding: 10px;'><b>Page {st.session_state.page_num + 1} of {total_pages}</b></div>",
                unsafe_allow_html=True
            )
        
        with col4:
            if st.button("Next ▶️", key="next_page", disabled=st.session_state.page_num >= total_pages - 1, use_container_width=True):
                st.session_state.page_num += 1
                st.rerun()
        
        with col5:
            if st.button("Last ⏭️", key="last_page", disabled=st.session_state.page_num >= total_pages - 1, use_container_width=True):
                st.session_state.page_num = total_pages - 1
                st.rerun()
        
        # Display paginated results
        paginated_results = paginate_dataframe(results, page_size, st.session_state.page_num)
        
        # Show records range
        start_record = st.session_state.page_num * page_size + 1
        end_record = min((st.session_state.page_num + 1) * page_size, len(results))
        st.info(f"Showing records {start_record:,} to {end_record:,} of {len(results):,}")
        
        # Display results in accordion format
        for idx, (_, row) in enumerate(paginated_results.iterrows()):
            display_result_accordion(row, start_record + idx - 1)
            
        
        # Also show as dataframe table
        st.markdown("---")
        st.markdown("### 📊 Table View")
        
        # Select columns to display in table
        display_cols = [col for col in results.columns if col != 'THE_LAW' and col != 'context']
        if display_cols:
            st.dataframe(
                paginated_results[display_cols],
                use_container_width=True,
                height=300
            )
        else:
            st.dataframe(paginated_results, use_container_width=True, height=300)
    
    else:
        st.warning("⚠️ No results found matching your search criteria")
        st.info("Try adjusting your filters or clearing them to see more results")
    
    # Footer with instructions
    st.markdown("---")
    st.markdown("""
    ### 📖 How to Use:
    
    1. **Load Data**: Upload a CSV file or enter a file path in the sidebar
    2. **Filter**: Use the search boxes to filter results:
       - Search in THE_LAW column (plain text search with word boundaries)
       - Search by article number or text
       - Search in context column (plain text search with word boundaries)
       - Filter by year (single year or range like 2015-2020)
       - Filter by language (English/French)
    3. **Browse**: Use pagination controls to navigate through results
    4. **View Details**: Click on accordion items to see full case details
    5. **Export**: Download filtered results as CSV
    
    ### ℹ️ Features:
    - ✅ File upload or manual path input
    - ✅ Multiple search filters (THE_LAW, article, context, year, language)
    - ✅ Plain text search with word boundaries
    - ✅ Accordion display with full case details
    - ✅ Pagination with customizable page sizes
    - ✅ CSV export of filtered results
    - ✅ Context highlighting and match counts
    """)

if __name__ == "__main__":
    main()
