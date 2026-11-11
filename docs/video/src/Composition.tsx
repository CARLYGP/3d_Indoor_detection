import React from "react";
import { AbsoluteFill, Composition, Still, useCurrentFrame, useVideoConfig } from "remotion";
import { TransitionSeries, springTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { slide } from "@remotion/transitions/slide";
import datos from "./datos.json";
import { Cierre, Entrada, Intro, Metricas, Pca, Perspectiva, Sala, Slam, Spatial, Superficies } from "./escenas";
import { Sala3D } from "./Sala3D";
import { C, Fondo, MONO, SANS } from "./tema";

const T = 20;
const ESCENAS: [string, React.FC, number][] = [
  ["Portada", Intro, 160],
  ["Entrada", Entrada, 160],
  ["SLAM3R", Slam, 170],
  ["PCA", Pca, 190],
  ["SpatialLM", Spatial, 250],
  ["Sala 3D", Sala, 330],
  ["Superficies", Superficies, 200],
  ["Perspectiva", Perspectiva, 170],
  ["Métricas", Metricas, 230],
  ["Cierre", Cierre, 140],
];
const DURACION = ESCENAS.reduce((s, e) => s + e[2], 0) - T * (ESCENAS.length - 1);

export const IndoorVideo: React.FC = () => (
  <TransitionSeries>
    {ESCENAS.flatMap(([nombre, Escena, dur], i) => {
      const nodos = [
        <TransitionSeries.Sequence key={nombre} name={nombre} durationInFrames={dur}>
          <Escena />
        </TransitionSeries.Sequence>,
      ];
      if (i < ESCENAS.length - 1)
        nodos.push(
          <TransitionSeries.Transition
            key={nombre + "-t"}
            presentation={(i % 2 === 0 ? fade() : slide({ direction: "from-right" })) as ReturnType<typeof fade>}
            timing={springTiming({ config: { damping: 200 }, durationInFrames: T })}
          />,
        );
      return nodos;
    })}
  </TransitionSeries>
);

export const PortadaBanner: React.FC = () => (
  <AbsoluteFill>
    <Fondo acento={C.violeta} />
    <AbsoluteFill>
      <Sala3D w={1600} h={640} cam={{ giro: 0.75, inclinacion: 0.62, distancia: 6.5, escala: 820, cx: 1190, cy: 330 }} grosor={2.2} tamEtiqueta={14} />
    </AbsoluteFill>
    <div style={{ position: "absolute", left: 90, top: 150 }}>
      <div style={{ fontFamily: MONO, fontSize: 22, letterSpacing: 4, color: C.violeta }}>VISIÓN 3D · LLM ESPACIAL</div>
      <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 84, lineHeight: 1.04, letterSpacing: -3, color: C.texto, marginTop: 18 }}>
        De un video
        <br />a una sala en 3D
      </div>
      <div style={{ fontFamily: SANS, fontSize: 28, color: C.tenue, marginTop: 22 }}>Reconstrucción con SLAM3R · detección con SpatialLM</div>
      <div style={{ display: "flex", gap: 16, marginTop: 40 }}>
        {[
          ["PAREDES", String(datos.nParedes), "#7DD3FC"],
          ["PUERTA", String(datos.puertas.length), C.ambar],
          ["OBJETOS", String(datos.cajas.length), C.violeta],
        ].map(([e, v, c]) => (
          <div key={e} style={{ padding: "16px 24px", borderRadius: 16, background: "rgba(8,12,22,0.72)", border: `1px solid ${c}66` }}>
            <div style={{ fontFamily: MONO, fontSize: 16, color: C.tenue, letterSpacing: 2 }}>{e}</div>
            <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 34, color: c }}>{v}</div>
          </div>
        ))}
      </div>
    </div>
  </AbsoluteFill>
);

/** Tarjeta animada del perfil: la sala detectada girando, sin texto repetido. */
export const TarjetaAnimada: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const giro = 0.2 + (frame / durationInFrames) * Math.PI * 2;
  return (
    <AbsoluteFill>
      <Fondo acento={C.violeta} />
      <AbsoluteFill>
        <Sala3D w={800} h={600} cam={{ giro, inclinacion: 0.66, distancia: 6.5, escala: 760, cx: 400, cy: 315 }} grosor={2.2} tamEtiqueta={15} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Composiciones: React.FC = () => (
  <>
    <Composition id="Indoor3D" component={IndoorVideo} durationInFrames={DURACION} fps={30} width={1920} height={1080} />
    <Still id="PortadaBanner" component={PortadaBanner} width={1600} height={640} />
    <Composition id="TarjetaAnimada" component={TarjetaAnimada} durationInFrames={240} fps={30} width={800} height={600} />
  </>
);
