const OVERPASS_URL = "https://overpass-api.de/api/interpreter";

const TAG_TO_CATEGORY = {
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

const CATEGORY_WEIGHTS = {
    business: { office: 3.0, bank: 1.5, conference: 1.0 },
    commercial: { restaurant: 2.0, cafe: 1.5, bar: 2.0, shop: 1.5, entertainment: 2.0 },
    residential_family: { school: 3.0, kindergarten: 3.0, park: 2.0, supermarket: 2.0, clinic: 1.5 },
    residential_single: { convenience: 2.0, laundry: 2.0, gym: 1.5, cafe: 1.0 },
    student: { university: 3.0, library: 2.0, cafe: 1.5, bookstore: 2.0 },
};

const TOWN_TYPE_LABELS = {
    business: "ビジネス街",
    commercial: "繁華街・商業地",
    residential_family: "ファミリー住宅街",
    residential_single: "単身者向け住宅街",
    student: "学生街",
    mixed: "複合エリア",
};

const LIVABILITY_CHECKS = {
    "買い物": ["supermarket", "convenience", "shop"],
    "飲食": ["restaurant", "cafe"],
    "医療": ["clinic", "hospital", "pharmacy"],
    "教育": ["school", "kindergarten", "library"],
    "公園・緑": ["park"],
    "交通": ["station", "bus_stop"],
};

const HOURLY_PATTERNS = {
    business: [0.005,0.003,0.002,0.002,0.003,0.010,0.040,0.100,0.130,0.100,0.070,0.060,0.065,0.060,0.055,0.050,0.045,0.060,0.050,0.035,0.025,0.015,0.010,0.005],
    commercial: [0.010,0.008,0.005,0.003,0.003,0.005,0.010,0.020,0.030,0.040,0.055,0.070,0.080,0.075,0.070,0.065,0.065,0.070,0.075,0.070,0.060,0.050,0.035,0.020],
    residential: [0.010,0.008,0.005,0.005,0.005,0.015,0.040,0.080,0.070,0.050,0.045,0.045,0.050,0.045,0.045,0.050,0.055,0.065,0.075,0.070,0.060,0.045,0.035,0.020],
};

// Map setup
const map = L.map("map").setView([35.6812, 139.7671], 13);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let marker = null;
let circle = null;
let selectedLat = null;
let selectedLon = null;

const analyzeBtn = document.getElementById("analyzeBtn");
const resultDiv = document.getElementById("result");
const radiusSelect = document.getElementById("radius");

map.on("click", (e) => {
    selectedLat = e.latlng.lat;
    selectedLon = e.latlng.lng;
    const radius = parseInt(radiusSelect.value);

    if (marker) map.removeLayer(marker);
    if (circle) map.removeLayer(circle);

    marker = L.marker(e.latlng).addTo(map);
    circle = L.circle(e.latlng, { radius, color: "#2563eb", fillOpacity: 0.08 }).addTo(map);

    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "この地点を分析する";
});

analyzeBtn.addEventListener("click", async () => {
    if (!selectedLat) return;
    const radius = parseInt(radiusSelect.value);
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "分析中...";
    resultDiv.textContent = "";

    const loading = document.createElement("div");
    loading.className = "loading";
    loading.textContent = "OSMデータを取得中...";
    resultDiv.appendChild(loading);

    try {
        const facilities = await fetchFacilities(selectedLat, selectedLon, radius);
        const profile = buildProfile(facilities);
        renderResult(profile, facilities);
    } catch (e) {
        resultDiv.textContent = "";
        const err = document.createElement("p");
        err.style.color = "red";
        err.textContent = "エラー: " + e.message;
        resultDiv.appendChild(err);
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "この地点を分析する";
    }
});

async function fetchFacilities(lat, lon, radius) {
    const query = `
[out:json][timeout:30];
(
  node(around:${radius},${lat},${lon})["amenity"];
  node(around:${radius},${lat},${lon})["shop"];
  node(around:${radius},${lat},${lon})["office"];
  node(around:${radius},${lat},${lon})["leisure"];
  node(around:${radius},${lat},${lon})["railway"="station"];
  node(around:${radius},${lat},${lon})["highway"="bus_stop"];
  way(around:${radius},${lat},${lon})["amenity"];
  way(around:${radius},${lat},${lon})["shop"];
  way(around:${radius},${lat},${lon})["office"];
  way(around:${radius},${lat},${lon})["leisure"="park"];
);
out center;`;

    const resp = await fetch(OVERPASS_URL, {
        method: "POST",
        body: "data=" + encodeURIComponent(query),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    const data = await resp.json();

    const counts = {};
    for (const el of data.elements || []) {
        const tags = el.tags || {};
        const cats = categorize(tags);
        for (const c of cats) {
            counts[c] = (counts[c] || 0) + 1;
        }
    }
    return counts;
}

function categorize(tags) {
    const results = [];
    for (const [key, cat] of Object.entries(TAG_TO_CATEGORY)) {
        const [k, v] = key.split("=");
        if (tags[k] === v) results.push(cat);
    }
    if (tags.cuisine === "ramen") results.push("ramen");
    if (results.length === 0) {
        if (tags.shop) results.push("shop");
        else if (tags.office) results.push("office");
    }
    return results;
}

function buildProfile(facilities) {
    const typeScores = {};
    for (const [type, weights] of Object.entries(CATEGORY_WEIGHTS)) {
        let score = 0;
        for (const [cat, w] of Object.entries(weights)) {
            score += (facilities[cat] || 0) * w;
        }
        typeScores[type] = score;
    }
    const maxScore = Math.max(...Object.values(typeScores), 1);
    for (const k of Object.keys(typeScores)) typeScores[k] /= maxScore;

    const primaryType = Object.entries(typeScores).sort((a, b) => b[1] - a[1])[0][0];

    const livability = {};
    for (const [label, cats] of Object.entries(LIVABILITY_CHECKS)) {
        const total = cats.reduce((s, c) => s + (facilities[c] || 0), 0);
        livability[label] = total === 0 ? 0 : Math.min(5, Math.log1p(total) / Math.log1p(20) * 5);
    }

    const hourly = computeHourly(typeScores);

    return { typeScores, primaryType, livability, hourly };
}

function computeHourly(typeScores) {
    const bw = typeScores.business || 0;
    const cw = Math.max(typeScores.commercial || 0, typeScores.student || 0);
    const rw = Math.max(typeScores.residential_family || 0, typeScores.residential_single || 0);
    const total = bw + cw + rw || 1;

    const hourly = [];
    for (let i = 0; i < 24; i++) {
        hourly.push(
            (HOURLY_PATTERNS.business[i] * bw +
             HOURLY_PATTERNS.commercial[i] * cw +
             HOURLY_PATTERNS.residential[i] * rw) / total
        );
    }
    return hourly;
}

function renderResult(profile, facilities) {
    const totalFacilities = Object.values(facilities).reduce((a, b) => a + b, 0);
    resultDiv.textContent = "";

    // Title
    const h2 = document.createElement("h2");
    h2.textContent = "分析結果";
    resultDiv.appendChild(h2);

    const townType = document.createElement("div");
    townType.className = "town-type";
    townType.textContent = TOWN_TYPE_LABELS[profile.primaryType];
    resultDiv.appendChild(townType);

    const countP = document.createElement("p");
    countP.style.fontSize = "0.85em";
    countP.style.color = "#666";
    countP.textContent = "施設数: " + totalFacilities;
    resultDiv.appendChild(countP);

    // 類型スコア
    const typeSection = createScoreSection("街の類型スコア");
    const sorted = Object.entries(profile.typeScores).sort((a, b) => b[1] - a[1]);
    for (const [type, score] of sorted) {
        typeSection.appendChild(createScoreRow(
            TOWN_TYPE_LABELS[type], score * 100, (score * 100).toFixed(0) + "%", "blue"
        ));
    }
    resultDiv.appendChild(typeSection);

    // 生活利便性
    const livSection = createScoreSection("生活利便性");
    for (const [label, score] of Object.entries(profile.livability)) {
        livSection.appendChild(createScoreRow(
            label, score * 20, score.toFixed(1), "green"
        ));
    }
    resultDiv.appendChild(livSection);

    // 施設タグ
    const facSection = document.createElement("div");
    facSection.className = "facilities";
    const facTitle = document.createElement("h3");
    facTitle.style.fontSize = "0.9em";
    facTitle.style.color = "#555";
    facTitle.style.marginBottom = "6px";
    facTitle.textContent = "施設内訳";
    facSection.appendChild(facTitle);

    const sortedFac = Object.entries(facilities).sort((a, b) => b[1] - a[1]).slice(0, 12);
    for (const [cat, count] of sortedFac) {
        const tag = document.createElement("span");
        tag.className = "facility-tag";
        tag.textContent = cat + ": " + count;
        facSection.appendChild(tag);
    }
    resultDiv.appendChild(facSection);

    // 時間帯チャート
    const hourlySection = document.createElement("div");
    hourlySection.className = "hourly-chart";
    const hourlyTitle = document.createElement("h3");
    hourlyTitle.style.cssText = "font-size:0.9em;color:#555;margin:12px 0 6px;";
    hourlyTitle.textContent = "時間帯別の賑わい推定";
    hourlySection.appendChild(hourlyTitle);

    const maxH = Math.max(...profile.hourly);
    for (let h = 0; h < 24; h++) {
        const pct = (profile.hourly[h] / maxH) * 100;
        const row = document.createElement("div");
        row.className = "hourly-row";

        const label = document.createElement("span");
        label.className = "hourly-label";
        label.textContent = String(h).padStart(2, "0") + ":00";
        row.appendChild(label);

        const barBg = document.createElement("div");
        barBg.className = "score-bar-bg";
        const bar = document.createElement("div");
        bar.className = "hourly-bar";
        bar.style.width = pct + "%";
        barBg.appendChild(bar);
        row.appendChild(barBg);

        hourlySection.appendChild(row);
    }
    resultDiv.appendChild(hourlySection);
}

function createScoreSection(title) {
    const section = document.createElement("div");
    section.className = "score-section";
    const h3 = document.createElement("h3");
    h3.textContent = title;
    section.appendChild(h3);
    return section;
}

function createScoreRow(label, pct, valText, colorClass) {
    const row = document.createElement("div");
    row.className = "score-row";

    const labelEl = document.createElement("span");
    labelEl.className = "score-label";
    labelEl.textContent = label;
    row.appendChild(labelEl);

    const barBg = document.createElement("div");
    barBg.className = "score-bar-bg";
    const bar = document.createElement("div");
    bar.className = "score-bar " + colorClass;
    bar.style.width = pct + "%";
    barBg.appendChild(bar);
    row.appendChild(barBg);

    const val = document.createElement("span");
    val.className = "score-val";
    val.textContent = valText;
    row.appendChild(val);

    return row;
}
