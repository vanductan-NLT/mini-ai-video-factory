"""
Video Plan Generator - Creates Remotion-Compatible Editing Plans

Orchestrates AI analysis to generate comprehensive video editing plans
that map directly to Remotion's TransitionSeries composition API.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import jsonschema

logger = logging.getLogger(__name__)


class VideoPlanGenerator:
    """
    Generates Remotion-compatible video editing plans from AI analysis.
    """
    
    def __init__(self, schema_path: str = "./config/plan_schema.json"):
        self.schema_path = schema_path
        self.schema = self._load_schema()
        
        # Component mapping for different scene types
        self.component_mapping = {
            'intro': {
                'background': ['MatrixRain', 'GradientShift', 'ParticleBackground'],
                'text': ['SlideText', 'KineticText'],
                'default_transition': 'slide'
            },
            'content': {
                'overlay': ['ContentScene', 'ChartAnimation'],
                'default_transition': 'wipe'
            },
            'key_point': {
                'text': ['NeonText', 'GlitchText'],
                'overlay': ['HighlightMarker', 'KeyPointCallout'],
                'default_transition': 'flip'
            },
            'outro': {
                'background': ['LiquidWave', 'GradientShift'],
                'text': ['SlideText'],
                'default_transition': 'fade'
            }
        }
    
    def _load_schema(self) -> Optional[Dict]:
        """Load JSON schema for validation."""
        try:
            if os.path.exists(self.schema_path):
                with open(self.schema_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load schema: {e}")
        return None
    
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
        Generate complete video editing plan.
        
        Args:
            job_id: Unique job identifier
            original_filename: Original video filename
            video_duration: Total video duration in seconds
            fps: Frames per second
            width: Video width
            height: Video height
            highlights: List of detected highlights
            transcript_segments: Transcript with timestamps
            
        Returns:
            Complete plan.json structure
        """
        total_frames = int(video_duration * fps)
        
        plan = {
            "composition": {
                "id": "GeneratedVideo",
                "width": width,
                "height": height,
                "fps": fps,
                "durationInFrames": total_frames
            },
            "metadata": {
                "video_id": job_id,
                "original_filename": original_filename,
                "created_at": datetime.utcnow().isoformat() + "Z"
            },
            "sequences": []
        }
        
        # Convert highlights to sequences
        for i, highlight in enumerate(highlights):
            sequence = self._create_sequence_from_highlight(
                highlight, i, fps, transcript_segments
            )
            plan["sequences"].append(sequence)
        
        # Validate non-overlapping frames
        plan = self._validate_and_fix_frames(plan, total_frames)
        
        # Validate against schema
        if self.schema:
            try:
                jsonschema.validate(plan, self.schema)
                logger.info("Plan validated successfully against schema")
            except jsonschema.ValidationError as e:
                logger.warning(f"Plan validation warning: {e.message}")
        
        return plan
    
    def _create_sequence_from_highlight(
        self,
        highlight: Dict[str, Any],
        index: int,
        fps: int,
        transcript_segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a sequence from a highlight."""
        start_frame = int(highlight['start_time'] * fps)
        end_frame = int(highlight['end_time'] * fps)
        duration_frames = end_frame - start_frame
        
        highlight_type = highlight['type']
        
        # Get text content from transcript for this time range
        text_content = self._extract_text_for_timerange(
            transcript_segments,
            highlight['start_time'],
            highlight['end_time']
        )
        
        sequence = {
            "id": f"seq_{index + 1}",
            "type": highlight_type,
            "durationInFrames": duration_frames,
            "startFrame": start_frame,
            "endFrame": end_frame,
            "highlight": {
                "importance": highlight['importance'],
                "reason": highlight['reason']
            },
            "layers": []
        }
        
        # Add layers based on type
        if highlight_type in ['intro', 'outro']:
            # Intro/outro: Background + Text
            sequence["layers"] = self._create_intro_outro_layers(
                highlight_type, text_content
            )
        else:
            # Content: Video + Overlay
            sequence["layers"] = self._create_content_layers(
                highlight_type, start_frame, end_frame, text_content
            )
        
        # Add transition (except for last sequence, handled in validation)
        sequence["transition"] = self._select_transition(highlight_type)
        
        return sequence
    
    def _create_intro_outro_layers(
        self,
        scene_type: str,
        text_content: str
    ) -> List[Dict[str, Any]]:
        """Create layers for intro or outro scene."""
        import random
        
        mapping = self.component_mapping.get(scene_type, {})
        background_options = mapping.get('background', ['MatrixRain'])
        text_options = mapping.get('text', ['SlideText'])
        
        background = random.choice(background_options)
        text_comp = random.choice(text_options)
        
        # Truncate text if too long
        display_text = text_content[:50] if text_content else (
            "Welcome to Our Video" if scene_type == 'intro' else "Thanks for Watching!"
        )
        
        return [
            {
                "type": "background",
                "component": background,
                "props": {}
            },
            {
                "type": "text",
                "component": text_comp,
                "props": {
                    "text": display_text,
                    "fontSize": "4rem" if scene_type == 'intro' else "3.5rem",
                    "color": "white"
                }
            }
        ]
    
    def _create_content_layers(
        self,
        scene_type: str,
        start_frame: int,
        end_frame: int,
        text_content: str
    ) -> List[Dict[str, Any]]:
        """Create layers for content scene (video + overlay)."""
        layers = [
            {
                "type": "video",
                "component": "OffthreadVideo",
                "props": {
                    "src": "staticFile('input.mp4')",
                    "startFrom": start_frame,
                    "endAt": end_frame,
                    "style": {
                        "width": "100%",
                        "height": "100%",
                        "objectFit": "cover"
                    }
                }
            },
            {
                "type": "overlay",
                "component": "ContentScene",
                "props": {},
                "style": {
                    "position": "absolute",
                    "top": 0,
                    "left": 0,
                    "width": "100%",
                    "height": "100%"
                }
            }
        ]
        
        return layers
    
    def _select_transition(self, scene_type: str) -> Dict[str, Any]:
        """Select appropriate transition for scene type."""
        mapping = self.component_mapping.get(scene_type, {})
        transition_type = mapping.get('default_transition', 'fade')
        
        transition = {
            "type": transition_type,
            "durationInFrames": 30
        }
        
        # Add direction for directional transitions
        if transition_type in ['slide', 'wipe']:
            directions = ['from-right', 'from-left', 'from-top', 'from-bottom']
            import random
            transition["direction"] = random.choice(directions)
        
        return transition
    
    def _extract_text_for_timerange(
        self,
        segments: List[Dict[str, Any]],
        start_time: float,
        end_time: float
    ) -> str:
        """Extract transcript text for a given time range."""
        relevant_text = []
        
        for seg in segments:
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', 0)
            
            # Check if segment overlaps with time range
            if seg_start < end_time and seg_end > start_time:
                relevant_text.append(seg.get('text', '').strip())
        
        return ' '.join(relevant_text)
    
    def _validate_and_fix_frames(
        self,
        plan: Dict[str, Any],
        total_frames: int
    ) -> Dict[str, Any]:
        """Validate and fix frame overlaps."""
        sequences = plan.get("sequences", [])
        
        if not sequences:
            return plan
        
        # Ensure no gaps or overlaps
        for i, seq in enumerate(sequences):
            if i == 0:
                seq["startFrame"] = 0
            else:
                # Start where previous ended
                seq["startFrame"] = sequences[i-1]["endFrame"]
            
            # Recalculate duration
            seq["durationInFrames"] = seq["endFrame"] - seq["startFrame"]
            
            # Ensure positive duration
            if seq["durationInFrames"] <= 0:
                seq["durationInFrames"] = 30  # Minimum 1 second at 30fps
                seq["endFrame"] = seq["startFrame"] + seq["durationInFrames"]
        
        # Remove transition from last sequence
        if sequences:
            if "transition" in sequences[-1]:
                del sequences[-1]["transition"]
        
        # Ensure last sequence doesn't exceed total duration
        if sequences:
            if sequences[-1]["endFrame"] > total_frames:
                sequences[-1]["endFrame"] = total_frames
                sequences[-1]["durationInFrames"] = (
                    sequences[-1]["endFrame"] - sequences[-1]["startFrame"]
                )
        
        return plan
    
    def save_plan(self, plan: Dict[str, Any], output_path: str) -> bool:
        """Save plan to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Plan saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save plan: {e}")
            return False
