"""
Natural Language Processing Service for Content Gap Analysis.
Extracts LSI keywords, topic clusters, and semantic entities.
"""
import re
from collections import Counter
from typing import List, Dict, Any, Set, Tuple

import httpx
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.models.database import ContentGapAnalysis

settings = get_settings()


class NLPContentAnalyzer:
    """
    Analyzes competitor content to extract semantic keywords and topics.
    Uses TF-IDF, RAKE, and entity extraction.
    """
    
    def __init__(self):
        self.stopwords = self._load_stopwords()
        self.ngram_ranges = [(1, 2), (2, 3)]  # Unigrams, bigrams, trigrams
    
    def _load_stopwords(self) -> Set[str]:
        """Load English stopwords."""
        common_stops = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
            'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there',
            'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
            'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no',
            'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then',
            'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
            'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first',
            'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these',
            'give', 'day', 'most', 'us', 'is', 'was', 'are', 'were', 'been',
            'has', 'had', 'did', 'does', 'doing', 'done', 'should', 'shall'
        }
        return common_stops
    
    async def analyze_content_gap(
        self,
        project_id: str,
        target_keyword: str,
        target_url: str,
        competitor_urls: List[str]
    ) -> ContentGapAnalysis:
        """
        Comprehensive content gap analysis.
        
        1. Extract content from target and competitors
        2. Generate keyword vectors
        3. Identify missing terms and topics
        4. Provide content recommendations
        """
        analysis = ContentGapAnalysis(
            project_id=project_id,
            target_keyword=target_keyword
        )
        
        try:
            # Fetch target content
            target_content = await self._fetch_content(target_url)
            target_terms = self._extract_terms(target_content)
            target_entities = self._extract_entities(target_content)
            
            # Fetch and analyze competitors
            competitor_term_sets = []
            all_competitor_terms = Counter()
            
            for comp_url in competitor_urls[:5]:  # Analyze top 5
                try:
                    comp_content = await self._fetch_content(comp_url)
                    comp_terms = self._extract_terms(comp_content)
                    competitor_term_sets.append(comp_terms)
                    all_competitor_terms.update(comp_terms)
                except Exception:
                    continue
            
            # Identify missing keywords
            missing_keywords = []
            for term, freq in all_competitor_terms.most_common(50):
                if term not in target_terms and len(term) > 3:
                    relevance = self._calculate_relevance(term, target_keyword)
                    competitor_usage = sum(1 for cs in competitor_term_sets if term in cs)
                    
                    missing_keywords.append({
                        "keyword": term,
                        "relevance_score": round(relevance, 3),
                        "competitor_usage": f"{competitor_usage}/{len(competitor_term_sets)}",
                        "frequency_in_competitors": freq
                    })
            
            analysis.missing_lsi_keywords = sorted(
                missing_keywords, 
                key=lambda x: x["relevance_score"], 
                reverse=True
            )[:30]
            
            # Generate topic clusters
            analysis.topic_clusters = self._generate_topic_clusters(
                all_competitor_terms, target_terms
            )
            
            # Entity analysis
            analysis.entities_present = list(target_entities)
            
            # Calculate recommendations
            analysis.suggested_word_count = self._estimate_optimal_length(competitor_term_sets)
            
            # Generate suggested headings
            analysis.suggested_headings = self._generate_headings(
                missing_keywords[:10]
            )
            
            await analysis.insert()
            
        except Exception as e:
            analysis.entities_missing = [str(e)]
        
        return analysis
    
    async def _fetch_content(self, url: str) -> str:
        """Fetch and extract text content from URL."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; SEOBot/1.0)"
            })
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text from main content areas
            text = soup.get_text(separator=' ', strip=True)
            return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.lower().strip()
    
    def _extract_terms(self, text: str) -> Counter:
        """Extract meaningful terms from text using TF-like scoring."""
        words = text.split()
        
        # Filter stopwords and short words
        filtered = [
            w for w in words 
            if w not in self.stopwords 
            and len(w) > 2 
            and w.isalpha()
        ]
        
        terms = Counter(filtered)
        
        # Add n-grams (phrases)
        for n in [2, 3]:
            phrases = [
                ' '.join(filtered[i:i+n]) 
                for i in range(len(filtered) - n + 1)
                if all(word not in self.stopwords for word in filtered[i:i+n])
            ]
            terms.update(phrases)
        
        return terms
    
    def _extract_entities(self, text: str) -> Set[str]:
        """Extract potential named entities (simplified)."""
        # Capitalized word sequences (basic entity detection)
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        entities = set(re.findall(pattern, text, re.IGNORECASE))
        return {e.lower() for e in entities if len(e) > 3}
    
    def _calculate_relevance(self, term: str, target_keyword: str) -> float:
        """Calculate semantic relevance score."""
        # Simple relevance based on co-occurrence potential
        target_words = set(target_keyword.lower().split())
        term_words = set(term.split())
        
        if not target_words or not term_words:
            return 1.0
        
        # Jaccard similarity
        intersection = target_words & term_words
        union = target_words | term_words
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _generate_topic_clusters(
        self, 
        competitor_terms: Counter, 
        target_terms: Set[str]
    ) -> List[Dict[str, Any]]:
        """Group related terms into topic clusters."""
        # Group by semantic similarity (simplified)
        clusters = {}
        
        for term, freq in competitor_terms.most_common(100):
            words = tuple(sorted(term.split()))
            key = words[0] if words else term
            
            if key not in clusters:
                clusters[key] = {
                    "topic": key,
                    "related_terms": [],
                    "present_in_target": key in target_terms,
                    "frequency": 0
                }
            
            clusters[key]["related_terms"].append({
                "term": term,
                "frequency": freq
            })
            clusters[key]["frequency"] += freq
        
        # Sort by frequency and take top clusters
        sorted_clusters = sorted(
            clusters.values(), 
            key=lambda x: x["frequency"], 
            reverse=True
        )[:10]
        
        return sorted_clusters
    
    def _estimate_optimal_length(self, competitor_term_sets: List[Counter]) -> int:
        """Estimate optimal content length based on competitors."""
        if not competitor_term_sets:
            return 1500
        
        # Estimate word count from term diversity
        lengths = [len(cs) * 30 for cs in competitor_term_sets]  # Rough estimate
        avg_length = sum(lengths) / len(lengths)
        
        # Recommend slightly above average
        return int(avg_length * 1.1)
    
    def _generate_headings(self, keywords: List[Dict]) -> List[str]:
        """Generate suggested heading structure."""
        headings = []
        
        for kw in keywords[:5]:
            keyword = kw["keyword"]
            words = keyword.split()
            
            if len(words) >= 2:
                # Capitalize each word for heading
                heading = ' '.join(w.capitalize() for w in words)
                headings.append(f"H2: {heading}")
        
        return headings
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        terms1 = set(self._extract_terms(text1).keys())
        terms2 = set(self._extract_terms(text2).keys())
        
        if not terms1 or not terms2:
            return 0.0
        
        intersection = terms1 & terms2
        return len(intersection) / (len(terms1) * len(terms2)) ** 0.5


class CompetitorIntelligenceService:
    """
    Real-time competitor monitoring and change detection.
    """
    
    def __init__(self):
        self.analyzer = NLPContentAnalyzer()
    
    async def detect_changes(
        self,
        project_id: str,
        competitor_url: str,
        previous_fingerprint: str
    ) -> Dict[str, Any]:
        """
        Detect content and ranking changes for a competitor.
        """
        try:
            current_content = await self.analyzer._fetch_content(competitor_url)
            current_fingerprint = hash(current_content) % (10 ** 12)
            
            changes = {
                "content_changed": str(current_fingerprint) != previous_fingerprint,
                "current_fingerprint": str(current_fingerprint),
                "word_count": len(current_content.split()),
                "detected_at": "now"
            }
            
            if changes["content_changed"]:
                # Extract new headings to understand what changed
                soup = BeautifulSoup(current_content, 'lxml')
                headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2'])]
                changes["current_headings"] = headings[:10]
            
            return changes
            
        except Exception as e:
            return {"error": str(e)}
