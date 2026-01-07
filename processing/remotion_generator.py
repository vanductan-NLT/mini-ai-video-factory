
import os
import subprocess
import logging
import json
import shutil
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)

class RemotionGenerator:
    def __init__(self, remotion_dir: str = "./remotion-video"):
        self.remotion_dir = remotion_dir
        self.output_dir = os.path.join(remotion_dir, "out")
        
        # Mapping of component names to their relative paths for imports
        self.component_paths = {
            "MatrixRain": "./components/background/MatrixRain",
            "LiquidWave": "./components/background/LiquidWave",
            "ParticleBackground": "./components/background/ParticleBackground",
            "GradientShift": "./components/background/GradientShift",
            "GeometricPattern": "./components/background/GeometricPattern",
            "SlideText": "./components/text/SlideText",
            "KineticText": "./components/text/KineticText",
            "GlitchText": "./components/text/GlitchText",
            "NeonText": "./components/text/NeonText",
            "TypewriterText": "./components/text/TypewriterText",
            "ChartAnimation": "./components/animation/ChartAnimation",
            "HighlightMarker": "./components/overlay/HighlightMarker",
            "ProgressBar": "./components/overlay/ProgressBar",
            "KeyPointCallout": "./components/overlay/KeyPointCallout"
        }

    def generate_from_plan(self, plan_path: str, video_path: str = None, output_file: str = "src/GeneratedVideo.tsx"):
        """
        Generate Remotion TSX from a detailed 3-track plan.json file.
        """
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Plan file not found: {plan_path}")
            
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = json.load(f)
            
        # Copy video file if provided
        if video_path and os.path.exists(video_path):
            public_dir = os.path.join(self.remotion_dir, "public")
            os.makedirs(public_dir, exist_ok=True)
            
            # Determine target filename from plan or default to input.mp4
            media_tracks = plan.get("tracks", {}).get("media", [])
            if media_tracks:
                source_name = media_tracks[0].get("source", "input.mp4")
                target_filename = os.path.basename(source_name)
            else:
                target_filename = "input.mp4"
                
            dest_video = os.path.join(public_dir, target_filename)
            shutil.copy2(video_path, dest_video)
            logger.info(f"Copied input video to {dest_video}")

        # 1. Collect required imports
        imports = self._get_imports_from_plan(plan)
        
        # 2. Build composition
        component_code = self._build_composition_code(plan)
        
        # 3. Write file
        full_content = "\n".join(imports) + "\n\n" + component_code
        output_path = os.path.join(self.remotion_dir, output_file)
        
        with open(output_path, "w", encoding='utf-8') as f:
            f.write(full_content)
            
        logger.info(f"Generated 3-track Remotion composition at {output_path}")
        return output_path

    def _get_imports_from_plan(self, plan: Dict[str, Any]) -> List[str]:
        """Dynamically generate import statements based on plan tracks."""
        used_components: Set[str] = set()
        
        tracks = plan.get("tracks", {})
        for track_name in tracks:
            for item in tracks[track_name]:
                name = item.get("name")
                if name and name != "MainVideo":
                    used_components.add(name)
            
        imports = [
            'import { Sequence, staticFile, AbsoluteFill } from "remotion";',
            'import { OffthreadVideo } from "remotion";',
            'import React from "react";'
        ]
        
        # Add component imports
        for comp in sorted(used_components):
            path = self.component_paths.get(comp)
            if path:
                imports.append(f'import {{ {comp} }} from "{path}";')
            else:
                logger.warning(f"Unknown component path for: {comp}")
                
        return imports

    def _build_composition_code(self, plan: Dict[str, Any]) -> str:
        """Build the main GeneratedVideo component with 3-track timeline."""
        fps = plan.get("project", {}).get("fps", 30)
        tracks = plan.get("tracks", {})
        
        code = "export const GeneratedVideo: React.FC = () => {\n"
        code += "  return (\n"
        code += "    <AbsoluteFill style={{ backgroundColor: 'black' }}>\n"
        
        # 1. Media Layer (Bottom)
        code += "      {/* Media Track */}\n"
        for item in tracks.get("media", []):
            start_frame = int(item.get("start", 0) * fps)
            duration_frames = int(item.get("duration", 0) * fps)
            volume = item.get("volume", 1.0)
            source = item.get("source", "input.mp4")
            # If source is a full path, just take the filename
            source_filename = os.path.basename(source)
            code += f"      <Sequence from={{{start_frame}}} durationInFrames={{{duration_frames}}}>\n"
            code += f'        <OffthreadVideo src={{staticFile("{source_filename}")}} volume={{{volume}}} />\n'
            code += "      </Sequence>\n"

        # 2. Background Layer
        code += "\n      {/* Background Track */}\n"
        for item in tracks.get("background", []):
            start_frame = int(item.get("start", 0) * fps)
            duration_frames = int(item.get("duration", 0) * fps)
            name = item.get("name")
            props = self._props_to_jsx(item.get("props", {}))
            code += f"      <Sequence from={{{start_frame}}} durationInFrames={{{duration_frames}}}>\n"
            code += f"        <{name}{props} />\n"
            code += "      </Sequence>\n"

        # 3. Overlays Layer (Top)
        code += "\n      {/* Overlays Track */}\n"
        for item in tracks.get("overlays", []):
            start_frame = int(item.get("start", 0) * fps)
            duration_frames = int(item.get("duration", 0) * fps)
            name = item.get("name")
            props = self._props_to_jsx(item.get("props", {}))
            code += f"      <Sequence from={{{start_frame}}} durationInFrames={{{duration_frames}}}>\n"
            code += f"        <{name}{props} />\n"
            code += "      </Sequence>\n"

        code += "    </AbsoluteFill>\n"
        code += "  );\n"
        code += "};\n"
        
        return code

    def _props_to_jsx(self, props: Dict[str, Any]) -> str:
        """Convert Python dictionary to JSX props string."""
        if not props:
            return ""
            
        parts = []
        for key, value in props.items():
            if isinstance(value, str):
                parts.append(f'{key}="{value}"')
            elif isinstance(value, bool):
                parts.append(f'{key}={{{str(value).lower()}}}')
            elif isinstance(value, (int, float, dict, list)):
                parts.append(f'{key}={{{json.dumps(value)}}}')
            else:
                parts.append(f'{key}={{{value}}}')
                
        return " " + " ".join(parts) if parts else ""

    def render_video(self, composition_id: str = "GeneratedVideo", output_filename: str = "output.mp4", props: Dict[str, Any] = None):
        """Run npx remotion render with optional props"""
        import platform
        npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
        
        cmd = [
            npx_cmd, "remotion", "render",
            composition_id,
            os.path.join("out", output_filename)
        ]

        if props:
            cmd.extend(["--props", json.dumps(props)])
        
        logger.info(f"Rendering video with command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, cwd=self.remotion_dir, check=True)
            return os.path.join(self.output_dir, output_filename)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error rendering video: {e}")
            raise
