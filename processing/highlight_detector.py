"""
Highlight Detection System for AI-Powered Video Editing

Multi-modal analysis to detect important moments in videos:
- Audio energy analysis
- Transcript sentiment analysis
- Visual change detection (placeholder)
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class HighlightDetector:
    """
    Detects highlight moments in videos using multi-modal analysis.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("GEMINI_API_KEY not found. Using rule-based detection only.")
            self.model = None
        
        # Configuration
        self.min_highlight_duration = 2.0  # seconds
        self.max_highlight_duration = 15.0  # seconds
        self.sensitivity = os.environ.get('HIGHLIGHT_SENSITIVITY', 'medium')
        
    def detect_highlights(
        self, 
        transcript_segments: List[Dict[str, Any]],
        audio_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect highlights from transcript and optionally audio.
        
        Args:
            transcript_segments: List of segments with 'start', 'end', 'text'
            audio_path: Optional path to audio file for energy analysis
            
        Returns:
            List of highlight dictionaries with:
            - type: intro, key_point, example, climax, outro
            - start_time: float
            - end_time: float
            - importance: float (0-1)
            - reason: str
        """
        if not transcript_segments:
            return self._create_default_highlights()
        
        highlights = []
        
        # Always create intro and outro
        duration = transcript_segments[-1]['end'] if transcript_segments else 10.0
        highlights.append(self._create_intro_highlight(transcript_segments))
        highlights.append(self._create_outro_highlight(transcript_segments, duration))
        
        # Detect key points using AI or rules
        if self.model:
            ai_highlights = self._detect_with_ai(transcript_segments)
            highlights.extend(ai_highlights)
        else:
            rule_highlights = self._detect_with_rules(transcript_segments)
            highlights.extend(rule_highlights)
        
        # Sort by start time
        highlights.sort(key=lambda x: x['start_time'])
        
        # Merge overlapping highlights
        highlights = self._merge_overlapping(highlights)
        
        logger.info(f"Detected {len(highlights)} highlights")
        return highlights
    
    def _detect_with_ai(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use Gemini AI to detect highlights from transcript."""
        try:
            # Combine transcript text with timestamps
            transcript_with_time = "\n".join([
                f"[{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}"
                for seg in segments
            ])
            
            prompt = f"""
            Analyze this video transcript to create a professional video editing plan.
            Identify key moments, high-impact quotes, and visual opportunities.
            
            For each highlight, provide:
            - type: 
                'key_point': Main educational/informative points.
                'callout': Moments requiring a text box or annotation on screen.
                'zoom': Significant statements where the camera should zoom in for emphasis.
                'impact_text': Short, punchy words (1-3 words) for flashy text effects.
                'transition': Natural topic shifts.
            - start_time / end_time: Precise timestamps in seconds.
            - text: The exact text from the transcript (for captions) or a summary for overlays.
            - importance: 0.0 to 1.0.
            - metadata: Additional info like 'zoom_level' (1.1-1.3), 'font_style', or 'effect_name'.
            
            Transcript:
            {transcript_with_time}
            
            Return ONLY a valid JSON array of objects:
            [
                {{
                    "type": "zoom",
                    "start_time": 12.4,
                    "end_time": 15.0,
                    "text": "The fastest way to change your life",
                    "importance": 0.9,
                    "metadata": {{ "zoom_level": 1.2, "effect": "smooth" }}
                }},
                {{
                    "type": "impact_text",
                    "start_time": 25.5,
                    "end_time": 27.0,
                    "text": "NEVER QUIT",
                    "importance": 0.95,
                    "metadata": {{ "style": "glitch" }}
                }}
            ]
            """
            
            response = self.model.generate_content(prompt)
            text_response = response.text
            
            # Extract JSON from response
            if "```json" in text_response:
                text_response = text_response.split("```json")[1].split("```")[0]
            elif "```" in text_response:
                text_response = text_response.split("```")[1].split("```")[0]
            
            import json
            highlights = json.loads(text_response.strip())
            
            logger.info(f"AI detected {len(highlights)} highlights")
            return highlights
            
        except Exception as e:
            logger.error(f"AI highlight detection failed: {e}")
            return self._detect_with_rules(segments)
    
    def _detect_with_rules(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback: Rule-based highlight detection."""
        highlights = []
        
        # Simple rule: Every ~10 seconds of content is a potential highlight
        for i, seg in enumerate(segments):
            if i % 3 == 1:  # Every 3rd segment approximately
                highlights.append({
                    'type': 'key_point',
                    'start_time': seg['start'],
                    'end_time': min(seg['end'], seg['start'] + 8.0),
                    'importance': 0.6,
                    'reason': 'Content segment'
                })
        
        return highlights
    
    def _create_intro_highlight(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create intro highlight."""
        if not segments:
            return {
                'type': 'intro',
                'start_time': 0,
                'end_time': 5.0,
                'importance': 0.9,
                'reason': 'Video introduction'
            }
        
        first_segment = segments[0]
        duration = min(5.0, first_segment['end'])
        
        return {
            'type': 'intro',
            'start_time': 0,
            'end_time': duration,
            'importance': 0.9,
            'reason': 'Video introduction'
        }
    
    def _create_outro_highlight(
        self, 
        segments: List[Dict[str, Any]], 
        total_duration: float
    ) -> Dict[str, Any]:
        """Create outro highlight."""
        outro_duration = 5.0
        start = max(0, total_duration - outro_duration)
        
        return {
            'type': 'outro',
            'start_time': start,
            'end_time': total_duration,
            'importance': 0.8,
            'reason': 'Video conclusion'
        }
    
    def _merge_overlapping(self, highlights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping or very close highlights."""
        if len(highlights) <= 1:
            return highlights
        
        merged = []
        current = highlights[0].copy()
        
        for next_h in highlights[1:]:
            # If overlapping or within 2 seconds
            if next_h['start_time'] <= current['end_time'] + 2.0:
                # Merge: extend current
                current['end_time'] = max(current['end_time'], next_h['end_time'])
                current['importance'] = max(current['importance'], next_h['importance'])
                # Keep the more specific type
                if next_h['type'] != 'key_point' and current['type'] == 'key_point':
                    current['type'] = next_h['type']
            else:
                merged.append(current)
                current = next_h.copy()
        
        merged.append(current)
        return merged
    
    def _create_default_highlights(self) -> List[Dict[str, Any]]:
        """Create default highlights when no transcript is available."""
        return [
            {
                'type': 'intro',
                'start_time': 0,
                'end_time': 5.0,
                'importance': 0.9,
                'reason': 'Default introduction'
            },
            {
                'type': 'content',
                'start_time': 5.0,
                'end_time': 10.0,
                'importance': 0.7,
                'reason': 'Main content'
            },
            {
                'type': 'outro',
                'start_time': 10.0,
                'end_time': 15.0,
                'importance': 0.8,
                'reason': 'Default conclusion'
            }
        ]
