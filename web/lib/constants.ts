export const OVERPASS_URL = "https://overpass-api.de/api/interpreter";

export const TAG_TO_CATEGORY: Record<string, string> = {
  "amenity=restaurant": "restaurant",
  "amenity=cafe": "cafe",
  "amenity=bar": "bar",
  "amenity=pub": "bar",
  "amenity=fast_food": "restaurant",
  "shop=supermarket": "supermarket",
  "shop=convenience": "convenience",
  "shop=mall": "shop",
  "shop=clothes": "shop",
  "shop=electronics": "shop",
  "shop=books": "bookstore",
  "shop=department_store": "shop",
  "office=company": "office",
  "office=government": "office",
  "office=it": "office",
  "amenity=bank": "bank",
  "amenity=school": "school",
  "amenity=university": "university",
  "amenity=college": "university",
  "amenity=kindergarten": "kindergarten",
  "amenity=library": "library",
  "amenity=clinic": "clinic",
  "amenity=hospital": "hospital",
  "amenity=pharmacy": "pharmacy",
  "leisure=park": "park",
  "leisure=fitness_centre": "gym",
  "shop=laundry": "laundry",
  "railway=station": "station",
  "highway=bus_stop": "bus_stop",
  "amenity=cinema": "entertainment",
  "amenity=theatre": "entertainment",
};

export const CATEGORY_WEIGHTS: Record<string, Record<string, number>> = {
  business: { office: 3.0, bank: 1.5, conference: 1.0 },
  commercial: {
    restaurant: 2.0,
    cafe: 1.5,
    bar: 2.0,
    shop: 1.5,
    entertainment: 2.0,
  },
  residential_family: {
    school: 3.0,
    kindergarten: 3.0,
    park: 2.0,
    supermarket: 2.0,
    clinic: 1.5,
  },
  residential_single: { convenience: 2.0, laundry: 2.0, gym: 1.5, cafe: 1.0 },
  student: { university: 3.0, library: 2.0, cafe: 1.5, bookstore: 2.0 },
};

export const TOWN_TYPE_LABELS: Record<string, string> = {
  business: "ビジネス街",
  commercial: "繁華街・商業地",
  residential_family: "ファミリー住宅街",
  residential_single: "単身者向け住宅街",
  student: "学生街",
  mixed: "複合エリア",
};

export const LIVABILITY_CHECKS: Record<string, string[]> = {
  買い物: ["supermarket", "convenience", "shop"],
  飲食: ["restaurant", "cafe"],
  医療: ["clinic", "hospital", "pharmacy"],
  教育: ["school", "kindergarten", "library"],
  "公園・緑": ["park"],
  交通: ["station", "bus_stop"],
};

export const HOURLY_PATTERNS: Record<string, number[]> = {
  business: [
    0.005, 0.003, 0.002, 0.002, 0.003, 0.01, 0.04, 0.1, 0.13, 0.1, 0.07,
    0.06, 0.065, 0.06, 0.055, 0.05, 0.045, 0.06, 0.05, 0.035, 0.025, 0.015,
    0.01, 0.005,
  ],
  commercial: [
    0.01, 0.008, 0.005, 0.003, 0.003, 0.005, 0.01, 0.02, 0.03, 0.04, 0.055,
    0.07, 0.08, 0.075, 0.07, 0.065, 0.065, 0.07, 0.075, 0.07, 0.06, 0.05,
    0.035, 0.02,
  ],
  residential: [
    0.01, 0.008, 0.005, 0.005, 0.005, 0.015, 0.04, 0.08, 0.07, 0.05, 0.045,
    0.045, 0.05, 0.045, 0.045, 0.05, 0.055, 0.065, 0.075, 0.07, 0.06, 0.045,
    0.035, 0.02,
  ],
};
