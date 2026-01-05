
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

    def analyze(self, transcript_text: str) -> List[Dict[str, Any]]:
        """
        Analyze transcript to identify scenes and suggest effects.
        Returns a list of scene definitions.
        """
        if not self.model:
            return self._mock_analysis(transcript_text)

        prompt = f"""
        Analyze the following video transcript and divide it into logical scenes.
        For each scene, suggest appropriate visual effects and transitions.
        
        Available Effects:
        - Intro: SlideText, MatrixRain
        - Content: TypewriterText, ChartAnimation, CircularProgress, AnimatedList, SoundWave, CardFlip
        - Outro: SlideText, LiquidWave
        
        Available Transitions:
        - slide, fade, wipe, flip, clockWipe
        
        Transcript:
        {transcript_text}
        
        Return ONLY valid JSON in the following format:
        [
            {{
                "type": "intro|content|outro",
                "start_time": 0.0,
                "end_time": 5.0,
                "text_content": "Summary of text",
                "suggested_effect": "EffectName",
                "suggested_transition": "TransitionName"
            }}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response (remove markdown code blocks if any)
            text_response = response.text
            if "```json" in text_response:
                text_response = text_response.split("```json")[1].split("```")[0]
            elif "```" in text_response:
                text_response = text_response.split("```")[1].split("```")[0]
                
            scenes = json.loads(text_response.strip())
            return scenes
        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
            return self._mock_analysis(transcript_text)

    def _mock_analysis(self, text: str) -> List[Dict[str, Any]]:
        """Mock analysis for testing or fallback"""
        # Simple split based on duration logic placeholder
        # In a real app, we would parse timestamps from the transcript source
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
