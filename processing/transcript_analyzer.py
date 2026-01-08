
import os
import json
import logging
import google.generativeai as genai
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("GEMINI_API_KEY not found. Using mock analysis.")
            self.model = None

    def analyze(self, transcript_text: str, srt_path: str = None) -> List[Dict[str, Any]]:
        """
        Analyze transcript and extract structured segments with timestamps.
        
        Args:
            transcript_text: Full transcript text
            srt_path: Optional path to SRT file for precise timestamps
            
        Returns:
            List of segments with 'start', 'end', 'text' keys
        """
        # Try to parse SRT for accurate timestamps
        if srt_path and os.path.exists(srt_path):
            segments = self._parse_srt(srt_path)
            if segments:
                logger.info(f"Parsed {len(segments)} segments from SRT")
                return segments
        
        # Fallback: create simple segments from text
        return self._create_segments_from_text(transcript_text)
    
    def _parse_srt(self, srt_path: str) -> List[Dict[str, Any]]:
        """Parse SRT file to extract segments with timestamps."""
        segments = []
        
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_segment = {}
            for line in lines:
                line = line.strip()
                
                if not line:
                    # Empty line marks end of subtitle
                    if current_segment and 'text' in current_segment:
                        segments.append(current_segment)
                        current_segment = {}
                    continue
                
                if '-->' in line:
                    # Timestamp line: 00:00:05,000 --> 00:00:10,000
                    parts = line.split('-->')
                    if len(parts) == 2:
                        current_segment['start'] = self._srt_time_to_seconds(parts[0].strip())
                        current_segment['end'] = self._srt_time_to_seconds(parts[1].strip())
                elif line.isdigit():
                    # Subtitle number, skip
                    continue
                else:
                    # Text content
                    if 'text' in current_segment:
                        current_segment['text'] += ' ' + line
                    else:
                        current_segment['text'] = line
            
            # Add last segment if exists
            if current_segment and 'text' in current_segment:
                segments.append(current_segment)
                
        except Exception as e:
            logger.error(f"Error parsing SRT: {e}")
            return []
        
        return segments
    
    def _srt_time_to_seconds(self, time_str: str) -> float:
        """Convert SRT timestamp to seconds."""
        # Format: 00:00:05,000
        try:
            time_part, ms_part = time_str.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            return h * 3600 + m * 60 + s + ms / 1000.0
        except:
            return 0.0
    
    def _create_segments_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Create simple segments from plain text (fallback)."""
        if not text:
            return []
        
        # Split by sentences or chunks
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        segments = []
        
        # Assume each sentence is ~3 seconds
        current_time = 0.0
        for i, sentence in enumerate(sentences):
            duration = 3.0  # Default duration per sentence
            segments.append({
                'start': current_time,
                'end': current_time + duration,
                'text': sentence
            })
            current_time += duration
        
        return segments

    def _mock_analysis(self, text: str) -> List[Dict[str, Any]]:
        """Mock analysis for testing or fallback"""
        # Simple split based on duration logic placeholder
        duration = 30 # Mock duration
        
        return [
            {
                "type": "intro",
                "start_time": 0,
                "end_time": 5,
                "text_content": "Welcome",
                "suggested_effect": "SlideText",
                "suggested_transition": "slide"
            },
            {
                "type": "content",
                "start_time": 5,
                "end_time": duration - 5,
                "text_content": "Content Body",
                "suggested_effect": "ChartAnimation",
                "suggested_transition": "wipe"
            },
            {
                "type": "outro",
                "start_time": duration - 5,
                "end_time": duration,
                "text_content": "Thanks for watching",
                "suggested_effect": "LiquidWave",
                "suggested_transition": "fade"
            }
        ]
