"""
Video Plan Generator - Creates detailed 3-track editing plans for Remotion.
Tracks: overlays, background, media.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class VideoPlanGenerator:
    """
    Generates structured video editing plans using 3 tracks: overlays, background, and media.
    Matches verified available components in the project.
    """
    
    def __init__(self):
        # List of verified available text/overlay components
        self.text_components = ["SlideText", "GlitchText", "NeonText", "TypewriterText", "KineticText"]
        self.overlay_components = ["KeyPointCallout", "HighlightMarker", "ProgressBar"]
        self.background_components = ["ParticleBackground", "LiquidWave", "GradientShift", "MatrixRain"]
    
    def generate_plan(
        self,
        job_id: str,
        original_filename: str,
        video_duration: float,
        fps: int,
        width: int,
        height: int,
        highlights: List[Dict[str, Any]],
        transcript_segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Produce a plan with 3 tracks: overlays, background, media.
        """
        plan = {
            "project": {
                "duration": round(video_duration, 2),
                "fps": fps,
                "width": width,
                "height": height,
                "jobId": job_id
            },
            "tracks": {
                "overlays": [],
                "background": [],
                "media": []
            }
        }
        
        # 1. Media Track (The core video)
        plan["tracks"]["media"].append({
            "start": 0.0,
            "duration": round(video_duration, 2),
            "type": "video",
            "name": "MainVideo",
            "source": original_filename,
            "volume": 1.0
        })
        
        # 2. Background Track
        # For a professional look, we add a subtle constant background effect
        plan["tracks"]["background"].append({
            "start": 0.0,
            "duration": round(video_duration, 2),
            "type": "background",
            "name": "ParticleBackground",
            "props": {
                "color": "rgba(255, 255, 255, 0.2)",
                "count": 40
            }
        })
        
        # 3. Overlays Track
        # Always add a progress bar at the top/bottom
        plan["tracks"]["overlays"].append({
            "start": 0.0,
            "duration": round(video_duration, 2),
            "type": "overlay",
            "name": "ProgressBar",
            "props": {}
        })
        
        # Process AI-detected highlights into overlays
        for i, hl in enumerate(highlights):
            h_type = hl.get('type')
            start = hl.get('start_time', 0)
            end = hl.get('end_time', start + 3)
            duration = round(end - start, 2)
            text = hl.get('text', hl.get('reason', 'Key Moment'))
            
            if h_type == 'impact_text':
                # Large flashy text
                name = "GlitchText" if hl.get('metadata', {}).get('style') == 'glitch' else "SlideText"
                plan["tracks"]["overlays"].append({
                    "start": round(start, 2),
                    "duration": duration,
                    "type": "text",
                    "name": name,
                    "props": {
                        "text": text.upper(),
                        "color": "#00f2ff" if name == "GlitchText" else "#ffffff",
                        "fontSize": "8rem"
                    }
                })
            
            elif h_type == 'callout' or h_type == 'key_point':
                # Callout box
                plan["tracks"]["overlays"].append({
                    "start": round(start, 2),
                    "duration": duration,
                    "type": "overlay",
                    "name": "KeyPointCallout",
                    "props": {
                        "text": text
                    }
                })
                
            elif h_type == 'zoom':
                # Special marker for human editors to see or logic to handle
                # For now, we center a SlideText to draw attention
                plan["tracks"]["overlays"].append({
                    "start": round(start, 2),
                    "duration": duration,
                    "type": "text",
                    "name": "SlideText",
                    "props": {
                        "text": text,
                        "fontSize": "5rem"
                    }
                })
        
        # Add basic captions from transcript segments for continuous engagement
        # Only add a few important ones to not clutter
        for i, seg in enumerate(transcript_segments):
            if i % 8 == 0: # Every few segments
                plan["tracks"]["overlays"].append({
                    "start": round(seg.get('start', 0), 2),
                    "duration": min(3.0, round(seg.get('end', 0) - seg.get('start', 0), 2)),
                    "type": "caption",
                    "name": "TypewriterText",
                    "props": {
                        "text": seg.get('text', ''),
                        "fontSize": "3rem"
                    }
                })

        # Clear out items that have 0 duration
        for track in plan["tracks"]:
            plan["tracks"][track] = [item for item in plan["tracks"][track] if item.get("duration", 0) > 0]
            
        logger.info(f"Generated detailed plan with {sum(len(t) for t in plan['tracks'].values())} elements across 3 tracks")
        return plan

    def save_plan(self, plan: Dict[str, Any], output_path: str) -> bool:
        """Save plan to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save plan: {e}")
            return False
