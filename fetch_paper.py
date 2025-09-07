import requests
import json
import csv
import time
import logging
from datetime import datetime
from pathlib import Path
import difflib
import re
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ieee_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# List of papers to track
PAPER_TITLES = [
    "Comparative Study for Monocular Depth Detection Models on Embedded Systems", #not the target paper, but for sanity check
    "The Core of Modern AI Models:A Comprehensive Review on Encoder-Decoder Transformer"
]

# Optional: known document id mapping for guaranteed detection
DOC_ID_MAP = {
    # "paper title": "doc_id"
}

CSV_FILE = Path("ieee_paper_search_results.csv")
MAX_RETRIES = 5
RETRY_DELAY = 2
BASE_DELAY = 1
MATCH_THRESHOLDS = [0.98, 0.90, 0.80, 0.70]

class IEEESearcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        })
        self._warm_session()
    
    def _warm_session(self):
        """Warm up session by visiting IEEE main page"""
        try:
            logger.info("Warming up session...")
            response = self.session.get("https://ieeexplore.ieee.org", timeout=10)
            time.sleep(BASE_DELAY)
            logger.info(f"Session warmed up, status: {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to warm up session: {e}")
    
    def normalize_title(self, title: str) -> str:
        """Enhanced title normalization"""
        if not title:
            return ""
        
        # Remove common punctuation and normalize whitespace
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove common stop words that might affect matching
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as'}
        words = normalized.split()
        filtered_words = [w for w in words if w not in stop_words or len(w) > 3]
        
        return ' '.join(filtered_words)
    
    def generate_search_variations(self, title: str) -> List[str]:
        """Generate multiple search query variations"""
        variations = []
        
        # Original title with quotes (phrase search)
        variations.append(f'"{title}"')
        
        # Original title without quotes
        variations.append(title)
        
        # Title with key terms
        words = title.split()
        if len(words) > 3:
            # Use first and last few words
            key_terms = ' '.join(words[:2] + words[-2:])
            variations.append(f'"{key_terms}"')
        
        # Remove common academic words and search
        academic_words = ['study', 'analysis', 'review', 'comprehensive', 'survey', 'evaluation']
        filtered_title = ' '.join([w for w in words if w.lower() not in academic_words])
        if filtered_title != title and len(filtered_title) > 10:
            variations.append(f'"{filtered_title}"')
        
        # Search by main topic keywords
        if 'depth' in title.lower() and 'monocular' in title.lower():
            variations.append('"monocular depth detection embedded"')
        elif 'transformer' in title.lower() and 'encoder' in title.lower():
            variations.append('"encoder decoder transformer AI"')
        
        return variations
    
    def search_ieee_api(self, query: str, max_results: int = 500) -> Optional[Dict[str, Any]]:
        """Search IEEE using REST API with pagination"""
        url = "https://ieeexplore.ieee.org/rest/search"
        
        headers = {
            "Origin": "https://ieeexplore.ieee.org",
            "Referer": "https://ieeexplore.ieee.org/search/searchresult.jsp",
            "Content-Type": "application/json"
        }
        
        all_records = []
        rows_per_page = 200
        start_record = 1
        
        while len(all_records) < max_results:
            payload = {
                "queryText": query,
                "highlight": True,
                "returnType": "SEARCH",
                "returnFacets": ["ALL"],
                "rowsPerPage": min(rows_per_page, max_results - len(all_records)),
                "startRecord": start_record,
                "newsearch": True
            }
            
            success = False
            for attempt in range(MAX_RETRIES):
                try:
                    logger.debug(f"Search attempt {attempt + 1} for query: {query[:50]}...")
                    response = self.session.post(url, headers=headers, 
                                               data=json.dumps(payload), timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        success = True
                        break
                    elif response.status_code == 418:
                        logger.warning(f"Rate limited (418), waiting {RETRY_DELAY * (attempt + 1)}s...")
                        time.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        logger.warning(f"HTTP {response.status_code}, retrying...")
                        time.sleep(RETRY_DELAY)
                        
                except Exception as e:
                    logger.warning(f"Request failed: {e}, retrying...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
            
            if not success:
                logger.error(f"Failed to search after {MAX_RETRIES} attempts")
                break
            
            records = data.get("records", [])
            if not records:
                break
                
            all_records.extend(records)
            
            # Check if we have more results
            total = data.get("totalRecords", 0)
            if len(all_records) >= total or len(records) < rows_per_page:
                break
                
            start_record += len(records)
            time.sleep(BASE_DELAY)  # Be nice to the API
        
        logger.info(f"Retrieved {len(all_records)} total records for query: {query[:50]}...")
        return {"totalRecords": len(all_records), "records": all_records}
    
    def fetch_metadata(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed metadata for a document"""
        url = f"https://ieeexplore.ieee.org/rest/document/{doc_id}/metadata"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 418:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.warning(f"Metadata fetch failed: {e}")
                time.sleep(RETRY_DELAY)
        
        return None
    
    def calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles using multiple methods"""
        norm1 = self.normalize_title(title1)
        norm2 = self.normalize_title(title2)
        
        # Sequence matcher similarity
        seq_sim = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        
        # Word overlap similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if words1 and words2:
            word_sim = len(words1.intersection(words2)) / len(words1.union(words2))
        else:
            word_sim = 0
        
        # Combined similarity (weighted average)
        combined = (seq_sim * 0.7) + (word_sim * 0.3)
        
        return combined
    
    def find_best_match(self, target_title: str, candidates: List[Dict]) -> Optional[Tuple[Dict, float]]:
        """Find the best matching paper from candidates"""
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            candidate_title = candidate.get("articleTitle", "")
            if not candidate_title:
                continue
            
            score = self.calculate_similarity(target_title, candidate_title)
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        return (best_match, best_score) if best_match else None
    
    def search_paper(self, title: str) -> Dict[str, Any]:
        """Comprehensive paper search using multiple strategies"""
        result = {
            "title": title,
            "found": False,
            "matched_title": "",
            "doc_id": "",
            "doi": "",
            "link": "",
            "method": "",
            "similarity_score": 0.0
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Searching for: {title}")
        logger.info(f"{'='*60}")
        
        # Strategy 1: Direct metadata lookup if doc ID is known
        if title in DOC_ID_MAP:
            doc_id = DOC_ID_MAP[title]
            logger.info(f"Using known doc ID: {doc_id}")
            metadata = self.fetch_metadata(doc_id)
            if metadata:
                result.update({
                    "found": True,
                    "matched_title": metadata.get("title", ""),
                    "doc_id": doc_id,
                    "doi": metadata.get("doi", ""),
                    "link": f"https://ieeexplore.ieee.org/document/{doc_id}",
                    "method": "direct-metadata",
                    "similarity_score": 1.0
                })
                logger.info(f"✓ Found via direct metadata lookup")
                return result
        
        # Strategy 2: Try multiple search variations
        search_variations = self.generate_search_variations(title)
        all_candidates = []
        
        for i, query in enumerate(search_variations, 1):
            logger.info(f"\nTrying search variation {i}/{len(search_variations)}: {query}")
            search_result = self.search_ieee_api(query)
            
            if search_result and search_result.get("records"):
                candidates = search_result["records"]
                logger.info(f"Found {len(candidates)} candidates")
                
                # Log first few candidates for debugging
                for j, candidate in enumerate(candidates[:5], 1):
                    cand_title = candidate.get("articleTitle", "")
                    cand_id = candidate.get("articleNumber", "")
                    score = self.calculate_similarity(title, cand_title)
                    logger.debug(f"  {j}. [{cand_id}] {cand_title[:80]}... (score: {score:.3f})")
                
                all_candidates.extend(candidates)
            else:
                logger.warning(f"No results for variation: {query}")
        
        if not all_candidates:
            logger.error("No candidates found with any search variation")
            return result
        
        # Remove duplicates based on document ID
        unique_candidates = {}
        for candidate in all_candidates:
            doc_id = candidate.get("articleNumber")
            if doc_id and doc_id not in unique_candidates:
                unique_candidates[doc_id] = candidate
        
        candidates_list = list(unique_candidates.values())
        logger.info(f"\nTotal unique candidates: {len(candidates_list)}")
        
        # Strategy 3: Find best match using similarity thresholds
        best_match_result = self.find_best_match(title, candidates_list)
        
        if best_match_result:
            best_candidate, best_score = best_match_result
            logger.info(f"Best match score: {best_score:.3f}")
            logger.info(f"Best match title: {best_candidate.get('articleTitle', '')}")
            
            # Try different thresholds
            for threshold in MATCH_THRESHOLDS:
                if best_score >= threshold:
                    doc_id = best_candidate.get("articleNumber")
                    
                    # Try to get metadata for verification
                    metadata = self.fetch_metadata(doc_id)
                    
                    if metadata:
                        # Verify with metadata title
                        meta_title = metadata.get("title", "")
                        meta_score = self.calculate_similarity(title, meta_title)
                        
                        if meta_score >= threshold:
                            result.update({
                                "found": True,
                                "matched_title": meta_title,
                                "doc_id": doc_id,
                                "doi": metadata.get("doi", ""),
                                "link": f"https://ieeexplore.ieee.org/document/{doc_id}",
                                "method": f"fuzzy-match-metadata (threshold: {threshold})",
                                "similarity_score": meta_score
                            })
                            logger.info(f"✓ Found via fuzzy matching with metadata (score: {meta_score:.3f})")
                            return result
                    
                    # Fallback to search result without metadata verification
                    result.update({
                        "found": True,
                        "matched_title": best_candidate.get("articleTitle", ""),
                        "doc_id": doc_id,
                        "doi": best_candidate.get("doi", ""),
                        "link": f"https://ieeexplore.ieee.org/document/{doc_id}",
                        "method": f"fuzzy-match-search (threshold: {threshold})",
                        "similarity_score": best_score
                    })
                    logger.info(f"✓ Found via fuzzy matching search only (score: {best_score:.3f})")
                    return result
        
        # Strategy 4: Substring matching as last resort
        normalized_target = self.normalize_title(title)
        for candidate in candidates_list:
            candidate_title = candidate.get("articleTitle", "")
            normalized_candidate = self.normalize_title(candidate_title)
            
            if (normalized_target in normalized_candidate or 
                normalized_candidate in normalized_target or
                any(word in normalized_candidate for word in normalized_target.split() if len(word) > 4)):
                
                doc_id = candidate.get("articleNumber")
                metadata = self.fetch_metadata(doc_id)
                
                result.update({
                    "found": True,
                    "matched_title": metadata.get("title", "") if metadata else candidate_title,
                    "doc_id": doc_id,
                    "doi": metadata.get("doi", "") if metadata else candidate.get("doi", ""),
                    "link": f"https://ieeexplore.ieee.org/document/{doc_id}",
                    "method": "substring-match",
                    "similarity_score": self.calculate_similarity(title, candidate_title)
                })
                logger.info(f"✓ Found via substring matching")
                return result
        
        logger.error(f"✗ No match found for: {title}")
        return result

def save_results_to_csv(results: List[Dict[str, Any]]):
    """Save search results to CSV file"""
    file_exists = CSV_FILE.exists()
    
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "date", "title", "found", "matched_title", "doc_id", 
            "doi", "link", "method", "similarity_score"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for result in results:
            row = {
                "date": datetime.now().isoformat(),
                **result
            }
            writer.writerow(row)

def main():
    """Main execution function"""
    logger.info("Starting IEEE paper search...")
    logger.info(f"Papers to search: {len(PAPER_TITLES)}")
    
    searcher = IEEESearcher()
    results = []
    
    for i, title in enumerate(PAPER_TITLES, 1):
        logger.info(f"\n[{i}/{len(PAPER_TITLES)}] Processing paper...")
        
        try:
            result = searcher.search_paper(title)
            results.append(result)
            
            if result["found"]:
                logger.info(f"SUCCESS: Found paper with method '{result['method']}'")
                logger.info(f"Matched title: {result['matched_title']}")
                logger.info(f"DOC ID: {result['doc_id']}")
                logger.info(f"Link: {result['link']}")
            else:
                logger.error(f"FAILED: Could not find paper")
            
            # Add delay between searches to be respectful
            if i < len(PAPER_TITLES):
                time.sleep(BASE_DELAY * 2)
                
        except Exception as e:
            logger.error(f"Error processing paper '{title}': {e}")
            results.append({
                "title": title,
                "found": False,
                "matched_title": "",
                "doc_id": "",
                "doi": "",
                "link": "",
                "method": f"error: {str(e)}",
                "similarity_score": 0.0
            })
    
    # Save results
    save_results_to_csv(results)
    logger.info(f"\nCompleted! Results saved to {CSV_FILE}")
    
    # Summary
    found_count = sum(1 for r in results if r["found"])
    logger.info(f"Summary: {found_count}/{len(results)} papers found")
    
    for result in results:
        status = "✓ FOUND" if result["found"] else "✗ NOT FOUND"
        logger.info(f"{status}: {result['title']}")

if __name__ == "__main__":
    main()