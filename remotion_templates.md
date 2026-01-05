Text:
Slide Text
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 * 
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export default function SlideText() {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const opacity = spring({
        frame,
        fps,
        from: 0,
        to: 1,
        durationInFrames: 30,
    });

    const slideX = spring({
        frame,
        fps,
        from: 200,
        to: 0,
        durationInFrames: 30,
        config: {
            damping: 12,
            mass: 0.5,
        },
    });

    return (
        <div
      style= {{
        position: "absolute",
            top: "50%",
                left: "50%",
                    transform: `translate(-50%, -50%) translateX(${slideX}px)`,
                        width: "100%",
                            textAlign: "center",
      }
}
    >
    <h1
        style={
    {
        opacity,
            color: "white",
                fontSize: "4rem",
                    fontWeight: "bold",
        }
}
      >
    Sliding Text!
        </h1>
        </div>
  );
}

Typewriter Subtitle
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 * 
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { interpolate, useCurrentFrame } from "remotion";

export default function TypewriterSubtitle() {
    const frame = useCurrentFrame();

    const text = "I like typing...";
    const visibleCharacters = Math.floor(
        interpolate(frame, [0, 45], [0, text.length], {
            extrapolateRight: "clamp",
        })
    );

    return (
        <div
      style= {{
        position: "absolute",
            top: "50%",
                left: "50%",
                    transform: "translate(-50%, -50%)",
                        width: "100%",
                            textAlign: "center",
                                padding: "2rem",
      }
}
    >
{
    text
        .slice(0, visibleCharacters)
        .split("")
        .map((char, index) => {
            const hue = 210 + (index * 40) / text.length;
            const isGlitching = frame % 30 === 0 && Math.random() > 0.7;

            return (
                <span
              key= { index }
            style = {{
                display: "inline-block",
                    fontFamily: "'Courier New', monospace",
                        fontSize: "3rem",
                            fontWeight: "bold",
                                color: `white`,

                                    transition: "all 0.05s ease-out",
              }
        }
            >
                { char === " " ? " " : char}
    </span>
          );
        })}
<span
        style={
    {
        fontSize: "3rem",
            color: "#60a5fa",
                opacity: frame % 15 < 7 ? 1 : 0,

                    marginLeft: "0.2rem",
                        verticalAlign: "middle",
        }
}
      >
        ▌
</span>
    </div>
  );
}

Background effect:
Matrix Rain
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 * 
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { random, useCurrentFrame, useVideoConfig } from "remotion";

export default function MatrixRain() {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*";
  const columns = Math.floor(width / 20);
  const drops = Array.from({ length: columns }).map((_, i) => ({
    x: i * 20,
    y: random(i) * height,
    speed: random(i) * 5 + 5,
    char: characters[Math.floor(random(i) * characters.length)],
  }));

  return (
    <div
      style={{
        width,
        height,
        background: "linear-gradient(45deg, #0a1933, #1e40af)",
        position: "relative",
      }}
    >
      {drops.map((drop, i) => {
        const y = (drop.y + frame * drop.speed) % height;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: drop.x,
              top: y,
              color: `rgba(255, 255, 255, ${1 - (y / height) * 0.6})`,
              fontSize: "25px",
              fontFamily: "monospace",
              fontWeight: "bold",
              textShadow: "0 0 8px rgba(59, 130, 246, 0.9)",
            }}
          >
            {characters[Math.floor((frame + i) / 5) % characters.length]}
          </div>
        );
      })}
    </div>
  );
}

Liquid Wave
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 * 
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { useCurrentFrame, useVideoConfig } from "remotion";

export default function LiquidWave() {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const numberOfPoints = 50;
  const points = Array.from({ length: numberOfPoints + 1 }).map((_, i) => {
    const x = (i / numberOfPoints) * width;
    const waveHeight = Math.sin(frame / 20 + i / 5) * 50;
    const y = height / 2 + waveHeight;
    return `${x},${y}`;
  });

  return (
    <svg width={width} height={height} style={{ background: "#111827" }}>
      <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1e3a8a" />
          <stop offset="100%" stopColor="#3b82f6" />
        </linearGradient>
      </defs>
      <path
        d={`M 0,${height} ${points.join(" ")} ${width},${height} Z`}
        fill="url(#gradient)"
        style={{
          filter: "blur(10px)",
        }}
      />
    </svg>
  );
}

Content animation
Cicular progress: 
// Template code for Circular Progress
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 *
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export default function CircularProgress() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Calculate progress based on frame
  const progress = interpolate(
    frame % 90,
    [0, 90],
    [0, 100],
    {
      extrapolateRight: "clamp",
    }
  );
  
  // Calculate rotation for the loading effect
  const rotation = (frame * 4) % 360;
  
  // Calculate radius and circumference
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;
  
  // Pulse effect
  const pulse = 1 + Math.sin(frame / 10) * 0.05;

  return (
    <div
      style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          position: "relative",
          width: "300px",
          height: "300px",
          transform: `scale(${pulse})`,
        }}
      >
        {/* Background circle */}
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 200 200"
          style={{
            position: "absolute",
            transform: "rotate(-90deg)",
          }}
        >
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth="12"
          />
        </svg>
        
        {/* Progress circle */}
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 200 200"
          style={{
            position: "absolute",
            transform: "rotate(-90deg)",
          }}
        >
          <circle
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke="url(#progressGradient)"
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
          
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#1e3a8a" />
            </linearGradient>
          </defs>
        </svg>
        
        {/* Rotating dots */}
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 200 200"
          style={{
            position: "absolute",
            transform: `rotate(${rotation}deg)`,
          }}
        >
          <circle
            cx="100"
            cy="20"
            r="8"
            fill="#3b82f6"
          />
        </svg>
        
        {/* Percentage text */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            fontSize: "3rem",
            fontWeight: "bold",
            color: "white",
          }}
        >
          {Math.round(progress)}%
        </div>
      </div>
    </div>
  );
}

Chart animation: 
// Template code for Chart Animation
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 *
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { interpolate, useCurrentFrame } from "remotion";

export default function ChartAnimation() {
  const frame = useCurrentFrame();

  // Sample data points (can be replaced with your actual data)
  const data = [
    { x: 0, y: 50, label: "Jan" },
    { x: 1, y: 80, label: "Feb" },
    { x: 2, y: 30, label: "Mar" },
    { x: 3, y: 70, label: "Apr" },
    { x: 4, y: 45, label: "May" },
    { x: 5, y: 90, label: "Jun" },
    { x: 6, y: 60, label: "Jul" },
    { x: 7, y: 75, label: "Aug" },
    { x: 8, y: 40, label: "Sep" },
    { x: 9, y: 85, label: "Oct" },
  ];

  // Color palette for bars
  const colors = [
    "#4361ee",
    "#3a0ca3",
    "#7209b7",
    "#f72585",
    "#4cc9f0",
    "#4895ef",
    "#560bad",
    "#b5179e",
    "#f15bb5",
    "#00b4d8",
  ];

  // Chart dimensions
  const chartWidth = 900;
  const chartHeight = 500;
  const padding = 60;

  // Scale data to fit chart dimensions
  const xScale = (x: number) =>
    (x / (data.length - 1)) * (chartWidth - padding * 2) + padding;
  const yScale = (y: number) =>
    chartHeight - padding - (y / 100) * (chartHeight - padding * 2);

  const barWidth = ((chartWidth - padding * 2) / data.length) * 0.7;

  return (
    <div
      style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "Inter, system-ui, sans-serif",
        background: "linear-gradient(to bottom right, #111827, #1f2937)",
      }}
    >
      <div
        style={{
          position: "relative",
          width: `${chartWidth}px`,
          height: `${chartHeight}px`,
          backgroundColor: "rgba(0, 0, 0, 0.2)",
          borderRadius: "16px",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.3)",
          overflow: "hidden",
          padding: "20px",
        }}
      >
        <svg width={chartWidth} height={chartHeight}>
          {/* X-axis line */}
          <line
            x1={padding}
            y1={chartHeight - padding}
            x2={chartWidth - padding}
            y2={chartHeight - padding}
            stroke="rgba(255, 255, 255, 0.2)"
            strokeWidth="2"
          />

          {/* X-axis labels */}
          {data.map((point, i) => (
            <text
              key={`x-label-${i}`}
              x={xScale(point.x)}
              y={chartHeight - padding + 25}
              textAnchor="middle"
              fill="rgba(255, 255, 255, 0.8)"
              fontSize="14"
              fontWeight="500"
            >
              {point.label}
            </text>
          ))}

          {/* Bar chart with animation and different colors */}
          {data.map((point, i) => {
            const barHeight = (point.y / 100) * (chartHeight - padding * 2);

            // Animation that grows bars from bottom
            const barProgress = interpolate(
              frame,
              [i * 3, 15 + i * 3],
              [0, 1],
              { extrapolateRight: "clamp" }
            );

            const currentHeight = barHeight * barProgress;
            const currentY = chartHeight - padding - currentHeight;

            return (
              <g key={`bar-${i}`}>
                <rect
                  x={xScale(point.x) - barWidth / 2}
                  y={currentY}
                  width={barWidth}
                  height={currentHeight}
                  fill={colors[i % colors.length]}
                  rx="6"
                  ry="6"
                  filter="url(#shadow)"
                />
                <text
                  x={xScale(point.x)}
                  y={currentY - 10}
                  textAnchor="middle"
                  fill="white"
                  fontSize="14"
                  fontWeight="bold"
                  opacity={barProgress > 0.9 ? 1 : 0}
                >
                  {point.y}
                </text>
              </g>
            );
          })}

          {/* Define shadow filter */}
          <defs>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="4" stdDeviation="4" floodOpacity="0.3" />
            </filter>
          </defs>
        </svg>

        {/* Chart title */}
        <div
          style={{
            position: "absolute",
            top: "25px",
            left: "50%",
            transform: "translateX(-50%)",
            fontSize: "28px",
            fontWeight: "bold",
            color: "white",
            textShadow: "0 2px 4px rgba(0,0,0,0.3)",
            letterSpacing: "-0.5px",
          }}
        >
          Monthly Performance
        </div>

        {/* Chart subtitle */}
        <div
          style={{
            position: "absolute",
            top: "60px",
            left: "50%",
            transform: "translateX(-50%)",
            fontSize: "16px",
            color: "rgba(255, 255, 255, 0.7)",
            textShadow: "0 1px 2px rgba(0,0,0,0.2)",
          }}
        >
          Data visualization for 2023
        </div>
      </div>
    </div>
  );
}

Sound wave: 
// Template code for Sound Wave
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 * 
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { random, useCurrentFrame, useVideoConfig } from "remotion";

export default function SoundWave() {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const BAR_COUNT = 40;
  const bars = Array.from({ length: BAR_COUNT }).map((_, i) => {
    const seed = i * 1000;
    const height =
      Math.abs(Math.sin(frame / 10 + i / 2)) * 100 + random(seed) * 50;

    return {
      height,
      hue: (i / BAR_COUNT) * 180 + frame,
    };
  });

  return (
    <div
      style={{
        width,
        height,

        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "4px",
        backdropFilter: "blur(8px)",
        boxShadow: "inset 0 0 100px rgba(59, 130, 246, 0.2)",
      }}
    >
      {bars.map((bar, i) => (
        <div
          key={i}
          style={{
            width: "12px",
            height: `${bar.height}px`,
            background: `white`,
            borderRadius: "6px",
            transition: "height 0.1s ease",
            boxShadow: `0 0 10px rgba(59, 130, 246, 0.6)`,
          }}
        />
      ))}
    </div>
  );
}

Animated list: 
// Template code for Animated List
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 *
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export default function AnimatedList() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Sample list items
  const items = [
    { name: "Item One", color: "#3b82f6" },
    { name: "Item Two", color: "#60a5fa" },
    { name: "Item Three", color: "#93c5fd" },
  ];

  return (
    <div
      style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        width: "100%",
        maxWidth: "600px",
        padding: "2rem",
      }}
    >
      {items.map((item, i) => {
        const delay = i * 5;

        // Slide in from left
        const slideX = spring({
          frame: frame - delay,
          fps,
          from: -100,
          to: 0,
          config: {
            damping: 12,
            mass: 0.5,
          },
        });

        // Fade in
        const opacity = spring({
          frame: frame - delay,
          fps,
          from: 0,
          to: 1,
          config: {
            damping: 12,
            mass: 0.5,
          },
        });

        // Scale up
        const scale = spring({
          frame: frame - delay,
          fps,
          from: 0.3,
          to: 1,
          config: {
            damping: 12,
            mass: 0.5,
          },
        });

        return (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              marginBottom: "1rem",
              transform: `translateX(${slideX}px) scale(${scale})`,
              opacity,
            }}
          >
            <div
              style={{
                width: "80px",
                height: "80px",
                borderRadius: "50%",
                backgroundColor: item.color,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
              }}
            />
            <span
              style={{
                color: "white",
                fontSize: "3.5rem",
                fontWeight: "500",
              }}
            >
              {item.name}
            </span>
          </div>
        );
      })}
    </div>
  );
}


Card flip: 
// Template code for Card Flip
/**
 * Free Remotion Template Component
 * ---------------------------------
 * This template is free to use in your projects!
 * Credit appreciated but not required.
 *
 * Created by the team at https://www.reactvideoeditor.com
 * 
 * Happy coding and building amazing videos! 🎉
 */

"use client";

import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export default function CardFlip() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const rotation = spring({
    frame,
    fps,
    from: 0,
    to: 360,
    config: {
      damping: 15,
      mass: 0.5,
    },
  });

  return (
    <div
      style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        perspective: "1000px",
      }}
    >
      <div
        style={{
          width: "300px",
          height: "400px",
          transform: `translate(-50%, -50%) rotateY(${rotation}deg)`,
          transformStyle: "preserve-3d",
          position: "relative",
        }}
      >
        <div
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            backfaceVisibility: "hidden",
            background: "linear-gradient(45deg, #1e3a8a, #3b82f6)",
            borderRadius: "20px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            fontSize: "2rem",
            fontWeight: "bold",
            color: "white",
          }}
        >
          Remotion 👋
        </div>
        <div
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            backfaceVisibility: "hidden",
            background: "linear-gradient(45deg, #1e3a8a, #3b82f6)",
            borderRadius: "20px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            fontSize: "2rem",
            fontWeight: "bold",
            color: "white",
            transform: "rotateY(180deg)",
          }}
        >
          Back
        </div>
      </div>
    </div>
  );
}

