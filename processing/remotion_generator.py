
import os
import subprocess
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RemotionGenerator:
    def __init__(self, remotion_dir: str = "./remotion-video"):
        self.remotion_dir = remotion_dir
        self.output_dir = os.path.join(remotion_dir, "out")

    def generate_composition(self, scenes: List[Dict[str, Any]], video_path: str = None, output_file: str = "src/GeneratedVideo.tsx"):
        """
        Generate a Remotion React component file based on the analyzed scenes.
        Also copies the input video to public folder for easy access.
        """
        # Copy video file if provided
        if video_path and os.path.exists(video_path):
            import shutil
            public_dir = os.path.join(self.remotion_dir, "public")
            os.makedirs(public_dir, exist_ok=True)
            dest_video = os.path.join(public_dir, "input.mp4")
            shutil.copy2(video_path, dest_video)
            logger.info(f"Copied input video to {dest_video}")

        imports = [
            'import { TransitionSeries, linearTiming } from "@remotion/transitions";',
            'import { slide } from "@remotion/transitions/slide";',
            'import { fade } from "@remotion/transitions/fade";',
            'import { wipe } from "@remotion/transitions/wipe";',
            'import { flip } from "@remotion/transitions/flip";',
            'import { clockWipe } from "@remotion/transitions/clock-wipe";',
            'import { IntroScene } from "./scenes/IntroScene";',
            'import { ContentScene } from "./scenes/ContentScene";',
            'import { OutroScene } from "./scenes/OutroScene";',
            'import { OffthreadVideo, staticFile } from "remotion";',
            'import React from "react";'
        ]
        
        component_code = """
export const GeneratedVideo: React.FC = () => {
  return (
    <TransitionSeries>
"""
        
        fps = 30
        
        for i, scene in enumerate(scenes):
            duration_sec = scene.get('end_time', 5) - scene.get('start_time', 0)
            duration_frames = int(duration_sec * fps)
            scene_type = scene.get('type')
            
            # Map scene type/effect to Component
            scene_component_code = ""
            
            if scene_type == 'intro':
                scene_component_code = f"<{self._scene_component_name(scene_type)} />"
            elif scene_type == 'outro':
                scene_component_code = f"<{self._scene_component_name(scene_type)} />"
            else: # Content scene - Input video + Overlay
                start_frame = int(scene.get('start_time', 0) * fps)
                scene_component_code = f"""
        <div style={{{{ flex: 1, backgroundColor: 'black' }}}}>
            <OffthreadVideo 
                src={{staticFile("input.mp4")}} 
                startFrom={{{start_frame}}}
                endAt={{{start_frame + duration_frames}}}
                style={{{{ width: "100%", height: "100%", objectFit: "cover" }}}}
            />
            <div style={{{{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}}}>
                <{self._scene_component_name(scene_type)} />
            </div>
        </div>"""
                
            component_code += f"""      <TransitionSeries.Sequence durationInFrames={{{duration_frames}}}>
        {scene_component_code}
      </TransitionSeries.Sequence>
"""
            
            # Add transition if not the last scene
            if i < len(scenes) - 1:
                transition_name = scene.get('suggested_transition', 'fade')
                transition_code = self._get_transition_code(transition_name)
                component_code += transition_code

        component_code += """    </TransitionSeries>
  );
};

"""
        
        full_content = "\n".join(imports) + "\n\n" + component_code
        
        output_path = os.path.join(self.remotion_dir, output_file)
        with open(output_path, "w") as f:
            f.write(full_content)
        
        logger.info(f"Generated Remotion composition at {output_path}")
        return output_path

    def _scene_component_name(self, type_name: str) -> str:
        if type_name == 'intro': return 'IntroScene'
        if type_name == 'outro': return 'OutroScene'
        return 'ContentScene'

    def _get_transition_code(self, name: str) -> str:
        """Helper to get transition JSX"""
        if name == "slide":
            return """      <TransitionSeries.Transition
        presentation={slide({ direction: "from-right" })}
        timing={linearTiming({ durationInFrames: 30 })}
      />
"""
        elif name == "wipe":
             return """      <TransitionSeries.Transition
        presentation={wipe({ direction: "from-top-left" })}
        timing={linearTiming({ durationInFrames: 30 })}
      />
"""
        elif name == "flip":
             return """      <TransitionSeries.Transition
        presentation={flip()}
        timing={linearTiming({ durationInFrames: 30 })}
      />
"""
        elif name == "clockWipe":
             return """      <TransitionSeries.Transition
        presentation={clockWipe({ width: 1920, height: 1080 })}
        timing={linearTiming({ durationInFrames: 30 })}
      />
"""
        else: # default fade
             return """      <TransitionSeries.Transition
        presentation={fade()}
        timing={linearTiming({ durationInFrames: 30 })}
      />
"""

    def render_video(self, composition_id: str = "GeneratedVideo", output_filename: str = "output.mp4"):
        """Run npx remotion render"""
        import platform
        npx_cmd = "npx.cmd" if platform.system() == "Windows" else "npx"
        
        cmd = [
            npx_cmd, "remotion", "render",
            composition_id,
            os.path.join("out", output_filename)
        ]
        
        logger.info(f"Rendering video with command: {' '.join(cmd)}")
        try:
            # Shell=True might help on some Windows setups if executable path is tricky, 
            # but usually npx.cmd is enough. 
            subprocess.run(cmd, cwd=self.remotion_dir, check=True)
            return os.path.join(self.output_dir, output_filename)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error rendering video: {e}")
            raise
