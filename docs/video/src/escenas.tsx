import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import datos from "./datos.json";
import { CAJAS, COLOR, NOMBRE, PAREDES, Sala3D } from "./Sala3D";
import { C, Encabezado, Fondo, MONO, SANS, Tarjeta, Visor, prog } from "./tema";

const camara = (frame: number, base = 0.6, vel = 0.006, cx = 960, cy = 600, escala = 2600) => ({
  giro: base + frame * vel,
  inclinacion: 0.62,
  distancia: 6.5,
  escala,
  cx,
  cy,
});

/** Figura del informe con marco, zoom lento y pie de foto. */
const Figura: React.FC<{ src: string; pie: string; x: number; y: number; w: number; h: number; desde?: number; color?: string; zoom?: number }> = ({ src, pie, x, y, w, h, desde = 0, color = C.cian, zoom = 0.08 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const a = prog(frame, desde, 28);
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, opacity: a, scale: interpolate(a, [0, 1], [0.97, 1]) }}>
      <div style={{ position: "absolute", inset: 0, borderRadius: 18, overflow: "hidden", background: "#0B1220", boxShadow: "0 40px 100px rgba(0,0,0,0.6)" }}>
        <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", scale: String(1 + zoom * (frame / durationInFrames)) }} />
      </div>
      <Visor a={prog(frame, desde + 8, 24)} color={color} />
      <div style={{ position: "absolute", left: 0, bottom: -46, fontFamily: MONO, fontSize: 21, color: C.tenue }}>{pie}</div>
    </div>
  );
};

const Puntos: React.FC<{ items: string[]; desde: number; color: string; top?: number }> = ({ items, desde, color, top = 320 }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ position: "absolute", left: 1150, top, width: 650, display: "flex", flexDirection: "column", gap: 30 }}>
      {items.map((t, i) => {
        const a = prog(frame, desde + i * 14, 26);
        return (
          <div key={t} style={{ display: "flex", gap: 22, alignItems: "flex-start", opacity: a, translate: `${(1 - a) * 40}px 0` }}>
            <div style={{ minWidth: 50, height: 50, borderRadius: 25, border: `2px solid ${color}`, color, fontFamily: MONO, fontSize: 22, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center" }}>{i + 1}</div>
            <div style={{ fontFamily: SANS, fontSize: 33, lineHeight: 1.3, color: C.texto, fontWeight: 500, paddingTop: 4 }}>{t}</div>
          </div>
        );
      })}
    </div>
  );
};

/* ---------------------------------------------------------------- Portada */
export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const sub = prog(frame, 40, 30);
  return (
    <AbsoluteFill>
      <Fondo acento={C.violeta} />
      <AbsoluteFill style={{ opacity: 0.35 }}>
        <Sala3D w={1920} h={1080} cam={camara(frame, 0.3, 0.008, 960, 560, 2100)} paredes={prog(frame, 0, 70)} objetos={(i) => prog(frame, 30 + i * 5, 25)} etiquetas={0} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(6,10,19,0.85) 0%, rgba(6,10,19,0.4) 45%, transparent 75%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        {["De un video", "a una sala en 3D"].map((l, i) => {
          const a = prog(frame, 10 + i * 9, 32);
          return (
            <div key={l} style={{ overflow: "hidden", paddingBottom: 8 }}>
              <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 116, lineHeight: 1.04, letterSpacing: -4, color: C.texto, translate: `0 ${(1 - a) * 150}px`, textAlign: "center" }}>{l}</div>
            </div>
          );
        })}
        <div style={{ fontFamily: SANS, fontSize: 38, color: C.tenue, marginTop: 26, opacity: sub, translate: `0 ${(1 - sub) * 20}px` }}>
          Reconstrucción con <span style={{ color: C.cian, fontWeight: 700 }}>SLAM3R</span> y detección con <span style={{ color: C.violeta, fontWeight: 700 }}>SpatialLM</span>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- Entrada */
export const Entrada: React.FC = () => (
  <AbsoluteFill>
    <Fondo acento={C.cian} />
    <Encabezado etiqueta="Paso 1 · Entrada" titulo="Solo un video del interior" color={C.cian} />
    <Figura src="01_video_entrada.jpg" pie="cuadro del video de entrada" x={120} y={270} w={960} h={588} />
    <Puntos color={C.cian} desde={20} items={["Sin cámaras de profundidad ni sensores", "Sin reentrenar ningún modelo", "Una GPU RTX 3050 de 4 GB"]} />
  </AbsoluteFill>
);

/* ---------------------------------------------------------------- SLAM3R */
export const Slam: React.FC = () => (
  <AbsoluteFill>
    <Fondo acento={C.cian} />
    <Encabezado etiqueta="Paso 2 · SLAM3R" titulo="El video se vuelve nube de puntos" color={C.cian} />
    <Figura src="02_nube_slam3r.jpg" pie="raw_slam3r.ply · nube densa reconstruida" x={120} y={270} w={760} h={668} zoom={0.12} />
    <Puntos color={C.cian} desde={20} items={["Estima la trayectoria de la cámara cuadro a cuadro", "Triangula una nube de puntos densa del espacio", "Pero sale sin escala métrica ni orientación fija"]} />
  </AbsoluteFill>
);

/* ---------------------------------------------------------------- PCA */
export const Pca: React.FC = () => {
  const frame = useCurrentFrame();
  const cruce = prog(frame, 70, 40);
  return (
    <AbsoluteFill>
      <Fondo acento={C.ambar} />
      <Encabezado etiqueta="Paso 3 · resize.py" titulo="Alinear la nube con PCA" color={C.ambar} />
      <div style={{ position: "absolute", left: 120, top: 270, width: 760, height: 668 }}>
        <div style={{ position: "absolute", inset: 0, borderRadius: 18, overflow: "hidden", background: "#0B1220", boxShadow: "0 40px 100px rgba(0,0,0,0.6)" }}>
          <Img src={staticFile("02_nube_slam3r.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", opacity: 1 - cruce }} />
          <Img src={staticFile("03_nube_alineada_pca.jpg")} style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", opacity: cruce }} />
        </div>
        <Visor a={prog(frame, 8, 24)} color={C.ambar} />
        <div style={{ position: "absolute", left: 0, bottom: -46, fontFamily: MONO, fontSize: 21, color: C.tenue }}>{cruce < 0.5 ? "antes: raw_slam3r.ply" : "después: resized.ply"}</div>
      </div>
      <Puntos color={C.ambar} desde={14} items={["Centra la nube en el origen", "Rota el eje principal vertical hacia Z", "Escala a la altura típica de una habitación", "Fija el piso en Z = 0"]} />
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- SpatialLM: texto */
export const Spatial: React.FC = () => {
  const frame = useCurrentFrame();
  const lineas: string[] = datos.lineas;
  const n = Math.floor(interpolate(frame, [20, 200], [0, lineas.length], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const corta = (l: string) => {
    const m = l.match(/^(\w+)=(\w+)\((.*)\)$/);
    if (!m) return l;
    const nums = m[3].split(",").map((v) => (isNaN(Number(v)) ? v : Number(v).toFixed(2)));
    return `${m[1]}=${m[2]}(${nums.join(", ")})`;
  };
  return (
    <AbsoluteFill>
      <Fondo acento={C.violeta} />
      <Encabezado etiqueta="Paso 4 · SpatialLM" titulo="Un LLM que lee nubes de puntos" color={C.violeta} />
      <Tarjeta style={{ position: "absolute", left: 120, top: 270, width: 1060, height: 690, padding: "30px 34px", overflow: "hidden", opacity: prog(frame, 0, 20) }}>
        <div style={{ fontFamily: MONO, fontSize: 20, color: C.tenue, marginBottom: 16 }}>detections.txt</div>
        {lineas.slice(0, n).map((l) => {
          const tipo = l.includes("=Wall(") ? "wall" : l.includes("=Door(") ? "door" : (l.match(/Bbox\((\w+)/)?.[1] ?? "");
          return (
            <div key={l} style={{ fontFamily: MONO, fontSize: 17.5, lineHeight: 1.5, color: C.texto, whiteSpace: "nowrap" }}>
              <span style={{ color: COLOR[tipo] ?? C.texto }}>{corta(l).split("(")[0]}</span>
              <span style={{ color: C.tenue }}>({corta(l).split("(").slice(1).join("(")}</span>
            </div>
          );
        })}
      </Tarjeta>
      <div style={{ position: "absolute", left: 1240, top: 300, width: 560, display: "flex", flexDirection: "column", gap: 24 }}>
        {[
          [datos.nParedes, "paredes", COLOR.wall],
          [datos.puertas.length, "puerta", COLOR.door],
          [datos.cajas.length, "objetos", COLOR.sofa],
        ].map(([v, t, col], i) => {
          const a = prog(frame, 40 + i * 18, 26);
          return (
            <Tarjeta key={String(t)} style={{ padding: "22px 34px", display: "flex", alignItems: "baseline", gap: 22, opacity: a, translate: `${(1 - a) * 40}px 0` }}>
              <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 76, color: String(col), minWidth: 90 }}>{v}</div>
              <div style={{ fontFamily: SANS, fontSize: 34, color: C.texto }}>{t}</div>
            </Tarjeta>
          );
        })}
        <div style={{ fontFamily: SANS, fontSize: 28, lineHeight: 1.4, color: C.tenue, opacity: prog(frame, 110, 30) }}>
          Un codificador geométrico resume la nube y el LLM escribe cada elemento como una línea con su posición, tamaño y giro.
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- Sala en 3D */
export const Sala: React.FC = () => {
  const frame = useCurrentFrame();
  const piso = prog(frame, 0, 30);
  const paredes = prog(frame, 20, 70);
  const puerta = prog(frame, 80, 20);
  return (
    <AbsoluteFill>
      <Fondo acento={C.violeta} />
      <Encabezado etiqueta="Las detecciones, en 3D" titulo="La sala reconstruida" color={C.violeta} />
      <AbsoluteFill>
        <Sala3D w={1920} h={1080} cam={camara(frame, 0.5, 0.006, 760, 580, 1150)} piso={piso} paredes={paredes} puerta={puerta} objetos={(i) => prog(frame, 100 + i * 12, 26)} etiquetas={prog(frame, 110, 20)} grosor={3} tamEtiqueta={22} />
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 1520, top: 300, display: "flex", flexDirection: "column", gap: 14 }}>
        {CAJAS.map((b, i) => {
          const a = prog(frame, 100 + i * 12, 20);
          return (
            <div key={b.id} style={{ display: "flex", gap: 14, alignItems: "center", fontFamily: MONO, fontSize: 24, color: C.texto, opacity: a, translate: `${(1 - a) * 30}px 0` }}>
              <div style={{ width: 16, height: 16, borderRadius: 4, border: `2.5px solid ${COLOR[b.clase]}` }} />
              {NOMBRE[b.clase] ?? b.clase}
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", left: 1520, top: 720, width: 330, lineHeight: 1.5, fontFamily: MONO, fontSize: 18, color: C.tenue, opacity: prog(frame, 40, 30) }}>
        {PAREDES.length} muros · altura {PAREDES[0].h.toFixed(2)}<br />leído de detections.txt
      </div>
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- Superficies y resultado */
export const Superficies: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Fondo acento={C.cian} />
      <Encabezado etiqueta="Pasos 5 y 6 · walls_to_surface.py + viz_total.py" titulo="Paredes como plano arquitectónico" color={C.cian} />
      <div style={{ position: "absolute", left: 120, top: 280, width: 760, height: 640 }}>
        <Tarjeta style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
          <Sala3D w={760} h={640} cam={{ giro: 0.9 + frame * 0.004, inclinacion: 1.05, distancia: 7, escala: 1900, cx: 380, cy: 330 }} relleno={0.55 * prog(frame, 10, 40)} etiquetas={0} objetos={() => 0} grosor={2} />
        </Tarjeta>
        <div style={{ position: "absolute", left: 0, bottom: -46, fontFamily: MONO, fontSize: 21, color: C.tenue }}>cada Wall(...) se vuelve un panel 3D</div>
      </div>
      <Figura src="06_visualizacion_final.jpg" pie="visualización final sobre la nube real" x={940} y={280} w={860} h={640} desde={30} />
    </AbsoluteFill>
  );
};

export const Perspectiva: React.FC = () => (
  <AbsoluteFill>
    <Fondo acento={C.violeta} />
    <Encabezado etiqueta="Resultado" titulo="Nube, objetos y estructura juntos" color={C.violeta} />
    <Figura src="07_vista_perspectiva.jpg" pie="vista en perspectiva" x={120} y={270} w={1000} h={600} zoom={0.15} color={C.violeta} />
    <Figura src="04_detecciones_spatiallm.jpg" pie="detecciones sobre la nube (vista superior)" x={1170} y={270} w={630} h={600} desde={20} color={C.violeta} />
  </AbsoluteFill>
);

/* ---------------------------------------------------------------- Métricas de referencia */
const LAYOUT = [
  ["pared", 68.9, 68.2],
  ["puerta", 49.1, 47.4],
  ["ventana", 47.0, 51.4],
] as const;
const OBJETOS = [
  ["cama", 96.8, 95.2],
  ["sofá", 66.9, 69.1],
  ["mesa de noche", 62.8, 67.0],
  ["mesa de centro", 56.4, 64.9],
  ["silla", 20.8, 32.3],
] as const;

export const Metricas: React.FC = () => {
  const frame = useCurrentFrame();
  const Barra: React.FC<{ fila: readonly [string, number, number]; i: number; desde: number }> = ({ fila, i, desde }) => {
    const a = prog(frame, desde + i * 6, 40);
    return (
      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr 80px", alignItems: "center", gap: 16, marginBottom: 16 }}>
        <div style={{ fontFamily: SANS, fontSize: 28, color: C.texto }}>{fila[0]}</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ height: 14, borderRadius: 7, width: `${fila[1] * a}%`, background: C.ambar }} />
          <div style={{ height: 14, borderRadius: 7, width: `${fila[2] * a}%`, background: C.cian }} />
        </div>
        <div style={{ fontFamily: MONO, fontSize: 20, color: C.tenue, lineHeight: 1.3 }}>
          {(fila[1] * a).toFixed(1)}
          <br />
          {(fila[2] * a).toFixed(1)}
        </div>
      </div>
    );
  };
  return (
    <AbsoluteFill>
      <Fondo acento={C.ambar} />
      <Encabezado etiqueta="F1 @ IoU 0.25 · reportado por los autores de SpatialLM" titulo="Qué tan bien detecta SpatialLM" />
      <Tarjeta style={{ position: "absolute", left: 120, top: 280, width: 800, padding: "34px 40px", opacity: prog(frame, 0, 20) }}>
        <div style={{ fontFamily: MONO, fontSize: 22, color: C.tenue, letterSpacing: 2, marginBottom: 26 }}>ESTRUCTURA</div>
        {LAYOUT.map((f, i) => <Barra key={f[0]} fila={f} i={i} desde={10} />)}
      </Tarjeta>
      <Tarjeta style={{ position: "absolute", left: 980, top: 280, width: 820, padding: "34px 40px", opacity: prog(frame, 10, 20) }}>
        <div style={{ fontFamily: MONO, fontSize: 22, color: C.tenue, letterSpacing: 2, marginBottom: 26 }}>OBJETOS (SELECCIÓN)</div>
        {OBJETOS.map((f, i) => <Barra key={f[0]} fila={f} i={i} desde={24} />)}
      </Tarjeta>
      <div style={{ position: "absolute", left: 120, top: 720, display: "flex", gap: 40, fontFamily: MONO, fontSize: 24, color: C.texto, opacity: prog(frame, 40, 20) }}>
        <span><span style={{ display: "inline-block", width: 18, height: 18, borderRadius: 9, background: C.ambar, marginRight: 10 }} />Llama-1B</span>
        <span><span style={{ display: "inline-block", width: 18, height: 18, borderRadius: 9, background: C.cian, marginRight: 10 }} />Qwen-0.5B</span>
      </div>
      <div style={{ position: "absolute", left: 120, right: 120, bottom: 90, fontFamily: SANS, fontSize: 30, lineHeight: 1.45, color: C.tenue, opacity: prog(frame, 70, 30) }}>
        Etiquetar a mano una nube 3D es muy costoso, así que estas son las métricas oficiales del modelo sobre su propio conjunto de validación, no medidas sobre esta sala.
      </div>
    </AbsoluteFill>
  );
};

/* ---------------------------------------------------------------- Cierre */
export const Cierre: React.FC = () => {
  const frame = useCurrentFrame();
  const a = prog(frame, 0, 30);
  return (
    <AbsoluteFill>
      <Fondo acento={C.violeta} />
      <AbsoluteFill style={{ opacity: 0.3 }}>
        <Sala3D w={1920} h={1080} cam={camara(frame, 1.6, 0.008, 960, 560, 2100)} etiquetas={0} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at center, rgba(6,10,19,0.9) 0%, transparent 70%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ overflow: "hidden", paddingBottom: 10 }}>
          <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 104, letterSpacing: -3.5, color: C.texto, translate: `0 ${(1 - a) * 130}px` }}>3D Indoor Detection</div>
        </div>
        <div style={{ fontFamily: MONO, fontSize: 28, color: C.violeta, opacity: prog(frame, 14, 30), marginTop: 10 }}>SLAM3R · PCA · SpatialLM · Open3D</div>
        <div style={{ fontFamily: MONO, fontSize: 24, color: C.tenue, opacity: prog(frame, 26, 30), marginTop: 36, padding: "12px 28px", border: `1px solid ${C.borde}`, borderRadius: 999 }}>github.com/CARLYGP/3d_Indoor_detection</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
