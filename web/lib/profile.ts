import {
  CATEGORY_WEIGHTS,
  LIVABILITY_CHECKS,
  HOURLY_PATTERNS,
} from "./constants";

export interface TownProfile {
  typeScores: Record<string, number>;
  primaryType: string;
  livability: Record<string, number>;
  hourly: number[];
  facilities: Record<string, number>;
  totalFacilities: number;
}

export function buildProfile(facilities: Record<string, number>): TownProfile {
  const typeScores: Record<string, number> = {};
  for (const [type, weights] of Object.entries(CATEGORY_WEIGHTS)) {
    let score = 0;
    for (const [cat, w] of Object.entries(weights)) {
      score += (facilities[cat] || 0) * w;
    }
    typeScores[type] = score;
  }

  const maxScore = Math.max(...Object.values(typeScores), 1);
  for (const k of Object.keys(typeScores)) {
    typeScores[k] /= maxScore;
  }

  const primaryType = Object.entries(typeScores).sort(
    (a, b) => b[1] - a[1]
  )[0][0];

  const livability: Record<string, number> = {};
  for (const [label, cats] of Object.entries(LIVABILITY_CHECKS)) {
    const total = cats.reduce((s, c) => s + (facilities[c] || 0), 0);
    livability[label] =
      total === 0
        ? 0
        : Math.min(5, (Math.log1p(total) / Math.log1p(20)) * 5);
  }

  const hourly = computeHourly(typeScores);
  const totalFacilities = Object.values(facilities).reduce(
    (a, b) => a + b,
    0
  );

  return { typeScores, primaryType, livability, hourly, facilities, totalFacilities };
}

function computeHourly(typeScores: Record<string, number>): number[] {
  const bw = typeScores.business || 0;
  const cw = Math.max(
    typeScores.commercial || 0,
    typeScores.student || 0
  );
  const rw = Math.max(
    typeScores.residential_family || 0,
    typeScores.residential_single || 0
  );
  const total = bw + cw + rw || 1;

  const hourly: number[] = [];
  for (let i = 0; i < 24; i++) {
    hourly.push(
      (HOURLY_PATTERNS.business[i] * bw +
        HOURLY_PATTERNS.commercial[i] * cw +
        HOURLY_PATTERNS.residential[i] * rw) /
        total
    );
  }
  return hourly;
}
