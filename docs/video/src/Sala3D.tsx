import React from "react";
import datos from "./datos.json";
import { C, MONO } from "./tema";

type V3 = [number, number, number];

export const PAREDES = datos.paredes;
export const PUERTAS = datos.puertas;
export const CAJAS = datos.cajas;

export const COLOR: Record<string, string> = {
  wall: "#7DD3FC",
  door: "#F5A524",
  painting: "#F43F5E",
  wall_decoration: "#A78BFA",
  sofa: "#818CF8",
  chair: "#34D399",
  coffee_table: "#FBBF24",
  cupboard: "#22D3EE",
  hand_sink: "#2DD4BF",
  mirror: "#F472B6",
};

export const NOMBRE: Record<string, string> = {
  painting: "cuadro",
  wall_decoration: "decoración",
  sofa: "sofá",
  chair: "silla",
  coffee_table: "mesa de centro",
  cupboard: "armario",
  hand_sink: "lavamanos",
  mirror: "espejo",
};

// centro de la sala para orbitar a su alrededor
const xs = PAREDES.flatMap((p) => [p.a[0], p.b[0]]);
const ys = PAREDES.flatMap((p) => [p.a[1], p.b[1]]);
const PISO = PAREDES[0].z;
const ALTO = PAREDES[0].h;
const CENTRO: V3 = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2, PISO + ALTO / 2];

/** Polígono del piso: recorre las paredes encadenando extremos. */
const POLIGONO: [number, number][] = (() => {
  const clave = (p: number[]) => `${p[0].toFixed(3)},${p[1].toFixed(3)}`;
  const resto = [...PAREDES];
  const camino: number[][] = [resto[0].a, resto[0].b];
  resto.splice(0, 1);
  while (resto.length) {
    const fin = clave(camino[camino.length - 1]);
    const k = resto.findIndex((p) => clave(p.a) === fin || clave(p.b) === fin);
    if (k < 0) break;
    const p = resto.splice(k, 1)[0];
    camino.push(clave(p.a) === fin ? p.b : p.a);
  }
  return camino.map((p) => [p[0], p[1]]);
})();

export type Camara = { giro: number; inclinacion: number; distancia: number; escala: number; cx: number; cy: number };

const proyectar = (p: V3, cam: Camara) => {
  const x = p[0] - CENTRO[0];
  const y = p[1] - CENTRO[1];
  const z = p[2] - CENTRO[2];
  const x1 = x * Math.cos(cam.giro) - y * Math.sin(cam.giro);
  const y1 = x * Math.sin(cam.giro) + y * Math.cos(cam.giro);
  const y2 = y1 * Math.cos(cam.inclinacion) - z * Math.sin(cam.inclinacion);
  const z2 = y1 * Math.sin(cam.inclinacion) + z * Math.cos(cam.inclinacion);
  const f = cam.escala / (cam.distancia + y2);
  return { x: cam.cx + x1 * f, y: cam.cy - z2 * f, d: y2 };
};

const esquinasCaja = (c: number[], s: number[], giro: number, alto = 1): V3[] => {
  const res: V3[] = [];
  for (const dz of [-1, 1])
    for (const [dx, dy] of [
      [-1, -1],
      [1, -1],
      [1, 1],
      [-1, 1],
    ]) {
      const lx = (dx * s[0]) / 2;
      const ly = (dy * s[1]) / 2;
      const base = c[2] - s[2] / 2;
      res.push([c[0] + lx * Math.cos(giro) - ly * Math.sin(giro), c[1] + lx * Math.sin(giro) + ly * Math.cos(giro), dz < 0 ? base : base + s[2] * alto]);
    }
  return res;
};
const ARISTAS_CAJA = [
  [0, 1], [1, 2], [2, 3], [3, 0],
  [4, 5], [5, 6], [6, 7], [7, 4],
  [0, 4], [1, 5], [2, 6], [3, 7],
];

/**
 * Sala reconstruida a partir de detections.txt.
 * piso / paredes / puerta: progreso 0..1; objetos(i): progreso 0..1 de cada caja; relleno: opacidad de los paneles de pared.
 */
export const Sala3D: React.FC<{
  w: number;
  h: number;
  cam: Camara;
  piso?: number;
  paredes?: number;
  puerta?: number;
  objetos?: (i: number) => number;
  etiquetas?: number;
  relleno?: number;
  grosor?: number;
  tamEtiqueta?: number;
}> = ({ w, h, cam, piso = 1, paredes = 1, puerta = 1, objetos = () => 1, etiquetas = 1, relleno = 0.12, grosor = 2.5, tamEtiqueta = 18 }) => {
  type Pieza = { d: number; el: React.ReactNode };
  const piezas: Pieza[] = [];

  PAREDES.forEach((p, i) => {
    const a = Math.max(0, Math.min(1, paredes * 1.6 - i * 0.06));
    if (a <= 0) return;
    const q = [
      proyectar([p.a[0], p.a[1], p.z], cam),
      proyectar([p.b[0], p.b[1], p.z], cam),
      proyectar([p.b[0], p.b[1], p.z + p.h * a], cam),
      proyectar([p.a[0], p.a[1], p.z + p.h * a], cam),
    ];
    const d = q.reduce((s, v) => s + v.d, 0) / 4;
    piezas.push({
      d,
      el: <polygon key={p.id} points={q.map((v) => `${v.x},${v.y}`).join(" ")} fill={COLOR.wall} fillOpacity={relleno} stroke={COLOR.wall} strokeOpacity={0.85} strokeWidth={grosor} strokeLinejoin="round" />,
    });
  });

  PUERTAS.forEach((pu) => {
    if (puerta <= 0) return;
    const pared = PAREDES.find((p) => p.id === pu.pared)!;
    const ang = Math.atan2(pared.b[1] - pared.a[1], pared.b[0] - pared.a[0]);
    const s = [pu.w, 0.04, pu.h * puerta];
    const c = [pu.c[0], pu.c[1], PISO + (pu.h * puerta) / 2];
    const e = esquinasCaja(c, s, ang).map((v) => proyectar(v, cam));
    const d = e.reduce((acc, v) => acc + v.d, 0) / 8 - 0.05;
    piezas.push({ d, el: <polygon key={pu.id} points={[e[0], e[1], e[5], e[4]].map((v) => `${v.x},${v.y}`).join(" ")} fill={COLOR.door} fillOpacity={0.3} stroke={COLOR.door} strokeWidth={grosor} /> });
  });

  CAJAS.forEach((b, i) => {
    const a = objetos(i);
    if (a <= 0) return;
    const e = esquinasCaja(b.c, b.s, b.giro, a).map((v) => proyectar(v, cam));
    const d = e.reduce((acc, v) => acc + v.d, 0) / 8;
    const col = COLOR[b.clase] ?? "#fff";
    const arriba = proyectar([b.c[0], b.c[1], b.c[2] - b.s[2] / 2 + b.s[2] * a + 0.08], cam);
    piezas.push({
      d,
      el: (
        <g key={b.id} opacity={Math.min(1, a * 2)}>
          <polygon points={[e[4], e[5], e[6], e[7]].map((v) => `${v.x},${v.y}`).join(" ")} fill={col} fillOpacity={0.12} />
          {ARISTAS_CAJA.map(([m, n], k) => (
            <line key={k} x1={e[m].x} y1={e[m].y} x2={e[n].x} y2={e[n].y} stroke={col} strokeWidth={grosor} strokeLinecap="round" style={{ filter: `drop-shadow(0 0 4px ${col}aa)` }} />
          ))}
          {etiquetas > 0 && (
            <g opacity={etiquetas * Math.min(1, a * 1.5)}>
              <rect x={arriba.x - (NOMBRE[b.clase] ?? b.clase).length * tamEtiqueta * 0.32 - 10} y={arriba.y - tamEtiqueta - 6} width={(NOMBRE[b.clase] ?? b.clase).length * tamEtiqueta * 0.64 + 20} height={tamEtiqueta + 12} rx={6} fill="rgba(6,10,19,0.85)" stroke={col} strokeOpacity={0.7} />
              <text x={arriba.x} y={arriba.y - 3} textAnchor="middle" fontFamily={MONO} fontSize={tamEtiqueta} fill={col}>
                {NOMBRE[b.clase] ?? b.clase}
              </text>
            </g>
          )}
        </g>
      ),
    });
  });

  piezas.sort((a, b) => b.d - a.d);
  const pisoP = POLIGONO.map(([x, y]) => proyectar([x, y, PISO], cam));
  const rejilla: React.ReactNode[] = [];
  for (let k = -2; k <= 5; k++) {
    const a1 = proyectar([k * 0.5 - 0.5, -1.6, PISO], cam);
    const a2 = proyectar([k * 0.5 - 0.5, 2.2, PISO], cam);
    const b1 = proyectar([-1.3, k * 0.5 - 0.5, PISO], cam);
    const b2 = proyectar([3.3, k * 0.5 - 0.5, PISO], cam);
    rejilla.push(<line key={`a${k}`} x1={a1.x} y1={a1.y} x2={a2.x} y2={a2.y} stroke="rgba(255,255,255,0.06)" />);
    rejilla.push(<line key={`b${k}`} x1={b1.x} y1={b1.y} x2={b2.x} y2={b2.y} stroke="rgba(255,255,255,0.06)" />);
  }
  return (
    <svg width={w} height={h} style={{ overflow: "visible" }}>
      <g opacity={piso}>{rejilla}</g>
      <polygon points={pisoP.map((v) => `${v.x},${v.y}`).join(" ")} fill={C.cian} fillOpacity={0.07 * piso} stroke={C.cian} strokeOpacity={0.5 * piso} strokeWidth={grosor} strokeDasharray="8 8" />
      {piezas.map((p) => p.el)}
    </svg>
  );
};
