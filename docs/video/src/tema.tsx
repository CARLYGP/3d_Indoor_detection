import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { loadFont } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

export const { fontFamily: SANS } = loadFont("normal", { weights: ["400", "500", "600", "700", "800"], subsets: ["latin", "latin-ext"] });
export const { fontFamily: MONO } = loadMono("normal", { weights: ["400", "500", "700"], subsets: ["latin"] });

export const C = {
  fondo: "#060A13",
  panel: "rgba(255,255,255,0.035)",
  borde: "rgba(255,255,255,0.09)",
  texto: "#EEF2FA",
  tenue: "#8D99B2",
  ambar: "#F5A524",
  indigo: "#818CF8",
  cian: "#22D3EE",
  rosa: "#F43F5E",
  violeta: "#A78BFA",
  verde: "#34D399",
};

export const salida = Easing.bezier(0.16, 1, 0.3, 1);

/** Progreso 0..1 con easing, empezando en `desde` (frames) y durando `dur` frames. */
export const prog = (frame: number, desde: number, dur: number, easing = salida) =>
  interpolate(frame, [desde, desde + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing });

/** Fondo común: degradado radial, rejilla de puntos y viñeta, con una deriva lenta. */
export const Fondo: React.FC<{ acento?: string }> = ({ acento = C.ambar }) => {
  const frame = useCurrentFrame();
  const x = 30 + Math.sin(frame / 90) * 6;
  const y = 20 + Math.cos(frame / 110) * 5;
  return (
    <AbsoluteFill style={{ backgroundColor: C.fondo }}>
      <AbsoluteFill style={{ background: `radial-gradient(1100px 700px at ${x}% ${y}%, ${acento}1F, transparent 70%)` }} />
      <AbsoluteFill style={{ background: `radial-gradient(900px 600px at ${100 - x}% ${100 - y}%, ${C.cian}14, transparent 70%)` }} />
      <AbsoluteFill
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.07) 1px, transparent 1px)",
          backgroundSize: "34px 34px",
          backgroundPosition: `${(frame * 0.15) % 34}px 0px`,
          maskImage: "radial-gradient(ellipse at center, black 30%, transparent 80%)",
        }}
      />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.75)" }} />
    </AbsoluteFill>
  );
};

/** Título de escena: etiqueta pequeña + título grande, con entrada desde abajo. */
export const Encabezado: React.FC<{ etiqueta: string; titulo: string; color?: string; desde?: number }> = ({
  etiqueta,
  titulo,
  color = C.ambar,
  desde = 0,
}) => {
  const frame = useCurrentFrame();
  const a = prog(frame, desde, 24);
  const b = prog(frame, desde + 5, 28);
  return (
    <div style={{ position: "absolute", left: 120, top: 84 }}>
      <div
        style={{
          fontFamily: MONO,
          fontSize: 22,
          letterSpacing: 4,
          textTransform: "uppercase",
          color,
          opacity: a,
          translate: `0 ${(1 - a) * 14}px`,
        }}
      >
        {etiqueta}
      </div>
      <div style={{ overflow: "hidden", paddingBottom: 6 }}>
        <div
          style={{
            fontFamily: SANS,
            fontWeight: 800,
            fontSize: 64,
            letterSpacing: -1.5,
            color: C.texto,
            translate: `0 ${(1 - b) * 80}px`,
          }}
        >
          {titulo}
        </div>
      </div>
    </div>
  );
};

/** Marco con esquinas tipo visor de cámara. */
export const Visor: React.FC<{ color?: string; grosor?: number; largo?: number; a?: number }> = ({
  color = C.ambar,
  grosor = 4,
  largo = 46,
  a = 1,
}) => {
  const l = largo * a;
  const base: React.CSSProperties = { position: "absolute", width: l, height: l, borderColor: color, borderStyle: "solid", opacity: a };
  return (
    <>
      <div style={{ ...base, left: -14, top: -14, borderWidth: `${grosor}px 0 0 ${grosor}px` }} />
      <div style={{ ...base, right: -14, top: -14, borderWidth: `${grosor}px ${grosor}px 0 0` }} />
      <div style={{ ...base, left: -14, bottom: -14, borderWidth: `0 0 ${grosor}px ${grosor}px` }} />
      <div style={{ ...base, right: -14, bottom: -14, borderWidth: `0 ${grosor}px ${grosor}px 0` }} />
    </>
  );
};

export const Tarjeta: React.FC<{ style?: React.CSSProperties; children: React.ReactNode; color?: string }> = ({
  style,
  children,
  color,
}) => (
  <div
    style={{
      background: C.panel,
      border: `1px solid ${color ? color + "55" : C.borde}`,
      borderRadius: 22,
      boxShadow: "0 30px 80px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.05)",
      ...style,
    }}
  >
    {children}
  </div>
);

export const useSegundos = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return frame / fps;
};

export const fmt = (n: number, dec = 1) => n.toLocaleString("es-CO", { minimumFractionDigits: dec, maximumFractionDigits: dec });
