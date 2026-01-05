---
image: /generated/articles-docs-transitions-presentations-slide.png
crumb: "@remotion/transitions - Presentations"
title: "slide()"
---

A presentation where the entering slide pushes out the exiting slide.

<Demo type="slide" />

## Example

```tsx twoslash title="SlideTransition.tsx"
import { AbsoluteFill } from "remotion";

const Letter: React.FC<{
  children: React.ReactNode;
  color: string;
}> = ({ children, color }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: color,
        opacity: 0.9,
        justifyContent: "center",
        alignItems: "center",
        fontSize: 200,
        color: "white",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
// ---cut---
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { slide } from "@remotion/transitions/slide";

const BasicTransition = () => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={40}>
        <Letter color="#0b84f3">A</Letter>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={slide()}
        timing={linearTiming({ durationInFrames: 30 })}
      />
      <TransitionSeries.Sequence durationInFrames={60}>
        <Letter color="pink">B</Letter>
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
```

## API

Takes an object with the following properties:

### `direction`

One of `from-left`, `from-right`, `from-top`, `from-bottom`.

```tsx twoslash title="TypeScript type"
import { SlideDirection } from "@remotion/transitions/slide";

const slideDirection: SlideDirection = "from-left";
```

### `enterStyle?`<AvailableFrom v="4.0.84"/>

The style of the container when the scene is is entering.

### `exitStyle?`<AvailableFrom v="4.0.84"/>

The style of the container when the scene is exiting.

## See also

- [Source code for this presentation](https://github.com/remotion-dev/remotion/blob/main/packages/transitions/src/presentations/slide.tsx)
- [Presentations](/docs/transitions/presentations)

---
image: /generated/articles-docs-transitions-presentations-fade.png
crumb: "@remotion/transitions - Presentations"
title: "fade()"
---

A simple fade animation. The incoming slide fades in over the outgoing slide, while the outgoing slide does not change. Works only if the incoming slide is fully opaque.

<Demo type="fade" />

## Example

```tsx twoslash title="FadeTransition.tsx"
import { AbsoluteFill } from "remotion";

const Letter: React.FC<{
  children: React.ReactNode;
  color: string;
}> = ({ children, color }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: color,
        opacity: 0.9,
        justifyContent: "center",
        alignItems: "center",
        fontSize: 200,
        color: "white",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
// ---cut---
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";

const BasicTransition = () => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={40}>
        <Letter color="#0b84f3">A</Letter>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={fade()}
        timing={linearTiming({ durationInFrames: 30 })}
      />
      <TransitionSeries.Sequence durationInFrames={60}>
        <Letter color="pink">B</Letter>
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
```

## API

An object which takes:

### `enterStyle?`<AvailableFrom v="4.0.84"/>

The style of the container element when the scene is is entering.

### `exitStyle?`<AvailableFrom v="4.0.84"/>

The style of the container element when the scene is exiting.

### `shouldFadeOutExitingScene?`<AvailableFrom v="4.0.166"/>

Whether the exiting scene should fade out or not. Default `false`.

:::note
The default is `false` because if both the entering and existing scene are semi-opaque, the whole scene will be semi-opaque, which will make the content underneath shine though.  
We recommend for transitioning between fully opaque scenes setting this to `false`.  
If the scenes are not fully covered (like fading between overlays), we recommend setting this to `false`.
:::

## See also

- [Source code for this presentation](https://github.com/remotion-dev/remotion/blob/main/packages/transitions/src/presentations/fade.tsx)
- [Presentations](/docs/transitions/presentations)

---
image: /generated/articles-docs-transitions-presentations-wipe.png
crumb: "@remotion/transitions - Presentations"
title: "wipe()"
---

A presentation where the entering slide slides over the exiting slide.

<Demo type="wipe" />

## Example

```tsx twoslash title="WipeTransition.tsx"
import { AbsoluteFill } from "remotion";

const Letter: React.FC<{
  children: React.ReactNode;
  color: string;
}> = ({ children, color }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: color,
        opacity: 0.9,
        justifyContent: "center",
        alignItems: "center",
        fontSize: 200,
        color: "white",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
// ---cut---
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { wipe } from "@remotion/transitions/wipe";

const BasicTransition = () => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={40}>
        <Letter color="#0b84f3">A</Letter>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={wipe()}
        timing={linearTiming({ durationInFrames: 30 })}
      />
      <TransitionSeries.Sequence durationInFrames={60}>
        <Letter color="pink">B</Letter>
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
```

## API

Takes an object with the following properties:

### `direction`

One of `from-left`, `from-top-left`, `from-top`, `from-top-right`, `from-right`, `from-bottom-right`, `from-bottom`, `from-bottom-left`.

```tsx twoslash title="TypeScript type"
import { WipeDirection } from "@remotion/transitions/wipe";

const wipeDirection: WipeDirection = "from-left";
```

### `outerEnterStyle?`<AvailableFrom v="4.0.84"/>

The style of the outer element when the scene is is entering.

### `outerExitStyle?`<AvailableFrom v="4.0.84"/>

The style of the outer element when the scene is exiting.

### `innerEnterStyle?`<AvailableFrom v="4.0.84"/>

The style of the inner element when the scene is entering.

### `innerExitStyle?`<AvailableFrom v="4.0.84"/>

The style of the inner element when the scene is exiting.

## See also

- [Source code for this presentation](https://github.com/remotion-dev/remotion/blob/main/packages/transitions/src/presentations/wipe.tsx)
- [Presentations](/docs/transitions/presentations)

---
image: /generated/articles-docs-transitions-presentations-flip.png
crumb: "@remotion/transitions - Presentations"
title: "flip()"
---

# flip()<AvailableFrom v="4.0.54"/>

A presentation where the exiting slide flips by 180 degrees, revealing the next slide on the back side.

<Demo type="flip" />

## Example

```tsx twoslash title="SlideTransition.tsx"
import { AbsoluteFill } from "remotion";

const Letter: React.FC<{
  children: React.ReactNode;
  color: string;
}> = ({ children, color }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: color,
        opacity: 0.9,
        justifyContent: "center",
        alignItems: "center",
        fontSize: 200,
        color: "white",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
// ---cut---
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { flip } from "@remotion/transitions/flip";

const BasicTransition = () => {
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={40}>
        <Letter color="#0b84f3">A</Letter>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={flip()}
        timing={linearTiming({ durationInFrames: 30 })}
      />
      <TransitionSeries.Sequence durationInFrames={60}>
        <Letter color="pink">B</Letter>
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
```

## API

Takes an object with the following properties:

### `direction`

One of `from-left`, `from-right`, `from-top`, `from-bottom`.

```tsx twoslash title="TypeScript type"
import { FlipDirection } from "@remotion/transitions/flip";

const flipDirection: FlipDirection = "from-left";
```

### `perspective?`

The CSS `perspective` of the flip animation. Defaults to `1000`.

### `outerEnterStyle?`<AvailableFrom v="4.0.84"/>

The style of the outer element when the scene is is entering.

### `outerExitStyle?`<AvailableFrom v="4.0.84"/>

The style of the outer element when the scene is exiting.

### `innerEnterStyle?`<AvailableFrom v="4.0.84"/>

The style of the inner element when the scene is entering.

### `innerExitStyle?`<AvailableFrom v="4.0.84"/>

The style of the inner element when the scene is exiting.

## See also

- [Source code for this presentation](https://github.com/remotion-dev/remotion/blob/main/packages/transitions/src/presentations/flip.tsx)
- [Presentations](/docs/transitions/presentations)

---
image: /generated/articles-docs-transitions-presentations-clock-wipe.png
crumb: "@remotion/transitions - Presentations"
title: "clockWipe()"
---

# clockWipe()<AvailableFrom v="4.0.74"/>

A presentation where the exiting slide is wiped out in a circular movement, revealing the next slide underneath it.

<Demo type="clock-wipe" />

## Example

```tsx twoslash title="ClockWipeTransition.tsx"
import { AbsoluteFill } from "remotion";

const Letter: React.FC<{
  children: React.ReactNode;
  color: string;
}> = ({ children, color }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: color,
        opacity: 0.9,
        justifyContent: "center",
        alignItems: "center",
        fontSize: 200,
        color: "white",
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
// ---cut---
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import { useVideoConfig } from "remotion";

const BasicTransition = () => {
  const { width, height } = useVideoConfig();

  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={40}>
        <Letter color="#0b84f3">A</Letter>
      </TransitionSeries.Sequence>
      <TransitionSeries.Transition
        presentation={clockWipe({ width, height })}
        timing={linearTiming({ durationInFrames: 30 })}
      />
      <TransitionSeries.Sequence durationInFrames={60}>
        <Letter color="pink">B</Letter>
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
```

## API

Accepts an object with the following options:

### `width`

Should be set to the width of the video.

### `height`

Should be set to the height of the video.

### `outerEnterStyle?`<AvailableFrom v="4.0.84"/>

The style of the outer element when the scene is is entering.

### `outerExitStyle?`<AvailableFrom v="4.0.84"/>

The style of the outer element when the scene is exiting.

### `innerEnterStyle?`<AvailableFrom v="4.0.84"/>

The style of the inner element when the scene is entering.

### `innerExitStyle?`<AvailableFrom v="4.0.84"/>

The style of the inner element when the scene is exiting.

## See also

- [Source code for this presentation](https://github.com/remotion-dev/remotion/blob/main/packages/transitions/src/presentations/clock-wipe.tsx)
- [Presentations](/docs/transitions/presentations)

