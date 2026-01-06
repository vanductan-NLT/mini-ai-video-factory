
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
            "ChartAnimation": "./components/animation/ChartAnimation",
            "ContentScene": "./scenes/ContentScene",
            "HighlightMarker": "./components/overlay/HighlightMarker",
            "ProgressBar": "./components/overlay/ProgressBar",
            "KeyPointCallout": "./components/overlay/KeyPointCallout"
        }

    def generate_from_plan(self, plan_path: str, video_path: str = None, output_file: str = "src/GeneratedVideo.tsx"):
        """
        Generate Remotion TSX from a plan.json file.
        """
        if not os.path.exists(plan_path):
            raise FileNotFoundError(f"Plan file not found: {plan_path}")
            
        with open(plan_path, 'r', encoding='utf-8') as f:
            plan = json.load(f)
            
        # Copy video file if provided
        if video_path and os.path.exists(video_path):
            public_dir = os.path.join(self.remotion_dir, "public")
            os.makedirs(public_dir, exist_ok=True)
            dest_video = os.path.join(public_dir, "input.mp4")
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
            
        logger.info(f"Generated professional Remotion composition at {output_path}")
        return output_path

    def _get_imports_from_plan(self, plan: Dict[str, Any]) -> List[str]:
        """Dynamically generate import statements based on plan content."""
        used_components: Set[str] = set()
        used_transitions: Set[str] = set()
        
        for seq in plan.get("sequences", []):
            for layer in seq.get("layers", []):
                comp = layer.get("component")
                if comp and comp != "OffthreadVideo":
                    used_components.add(comp)
            
            trans = seq.get("transition")
            if trans:
                used_transitions.add(trans.get("type"))
                
        imports = [
            'import { TransitionSeries, linearTiming } from "@remotion/transitions";',
            'import { OffthreadVideo, staticFile, AbsoluteFill } from "remotion";',
            'import React from "react";'
        ]
        
        # Add transition imports
        for t in used_transitions:
            imports.append(f'import {{ {t} }} from "@remotion/transitions/{t}";')
            
        # Add component imports
        for comp in used_components:
            path = self.component_paths.get(comp)
            if path:
                imports.append(f'import {{ {comp} }} from "{path}";')
            else:
                logger.warning(f"Unknown component path for: {comp}")
                
        return imports

    def _build_composition_code(self, plan: Dict[str, Any]) -> str:
        """Build the main GeneratedVideo component body."""
        sequences = plan.get("sequences", [])
        
        code = "export const GeneratedVideo: React.FC = () => {\n"
        code += "  return (\n"
        code += "    <TransitionSeries>\n"
        
        for i, seq in enumerate(sequences):
            duration = seq.get("durationInFrames", 30)
            seq_id = seq.get("id", f"seq_{i}")
            
            code += f"      {{/* {seq_id} - {seq.get('type')} */}}\n"
            code += f"      <TransitionSeries.Sequence durationInFrames={{{duration}}}>\n"
            
            # Use AbsoluteFill for intro/outro/content layers
            code += "        <AbsoluteFill>\n"
            
            for layer in seq.get("layers", []):
                code += self._render_layer(layer)
                
            code += "        </AbsoluteFill>\n"
            code += "      </TransitionSeries.Sequence>\n\n"
            
            # Add transition
            trans = seq.get("transition")
            if trans and i < len(sequences) - 1:
                t_type = trans.get("type", "fade")
                t_dur = trans.get("durationInFrames", 30)
                t_dir = trans.get("direction")
                
                presentation = f"{t_type}({{ direction: '{t_dir}' }})" if t_dir else f"{t_type}()"
                
                code += f"      <TransitionSeries.Transition\n"
                code += f"        presentation={{{presentation}}}\n"
                code += f"        timing={{linearTiming({{ durationInFrames: {t_dur} }})}}\n"
                code += f"      />\n\n"
                
        code += "    </TransitionSeries>\n"
        code += "  );\n"
        code += "};\n"
        
        return code

    def _render_layer(self, layer: Dict[str, Any]) -> str:
        """Convert a layer object to JSX code."""
        comp = layer.get("component")
        props = layer.get("props", {})
        style = layer.get("style", {})
        
        jsx_props = self._props_to_jsx(props)
        jsx_style = ""
        if style:
            jsx_style = f" style={{{json.dumps(style)}}}"
            
        if comp == "OffthreadVideo":
            return f"          <OffthreadVideo{jsx_props}{jsx_style} />\n"
        
        if style:
            return f"          <div{jsx_style}>\n            <{comp}{jsx_props} />\n          </div>\n"
        else:
            return f"          <{comp}{jsx_props} />\n"

    def _props_to_jsx(self, props: Dict[str, Any]) -> str:
        """Convert Python dictionary to JSX props string."""
        if not props:
            return ""
            
        parts = []
        for key, value in props.items():
            if isinstance(value, str):
                if value.startswith("staticFile("):
                    # Handle staticFile calls
                    parts.append(f'{key}={{{value}}}')
                else:
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
