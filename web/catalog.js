const form = document.querySelector("form");
const query = document.querySelector("#query");
const category = document.querySelector("#category");
const cards = document.querySelector("#cards");
const status = document.querySelector("#status");
const useCases = new Map([
  [95, "축제 포스터 공공 제안서"],
  [142, "축제 포스터"],
  [143, "축제 포스터"],
  [344, "공공 제안서 예산 성과지표"],
  [346, "공공 제안서 일정"],
]);

const normalize = (value) => value.normalize("NFC").toLowerCase();
const assetPath = (path) => path.split("/").map(encodeURIComponent).join("/");
const number = (row) => String(row.id).padStart(3, "0");

function makeCard(row) {
  const item = document.createElement("li");
  const link = document.createElement("a");
  link.href = assetPath(row.image);
  const image = document.createElement("img");
  image.src = assetPath(row.thumbnail);
  image.alt = `${number(row)} ${row.name_ko} 원본 카드 열기`;
  image.loading = "lazy";
  link.append(image);
  const heading = document.createElement("h2");
  heading.textContent = `${number(row)} ${row.name_ko}`;
  const description = document.createElement("p");
  description.textContent = row.desc;
  const copy = document.createElement("button");
  copy.type = "button";
  copy.textContent = "번호와 설명 복사";
  copy.addEventListener("click", async () => {
    const text = `${heading.textContent} — ${row.desc}`;
    try {
      await navigator.clipboard.writeText(text);
      copy.textContent = "복사됨";
    } catch {
      window.prompt("아래 문구를 직접 복사하세요.", text);
    }
  });
  item.append(link, heading, description, copy);
  return item;
}

async function loadCatalog() {
  const response = await fetch("catalog.json");
  if (!response.ok) throw new Error(response.status);
  const rows = await response.json();
  const categories = new Map(rows.map((row) => [row.category_slug, row.category]));
  for (const [slug, label] of categories) category.add(new Option(label, slug));

  const entries = rows.map((row) => ({
    row,
    text: normalize([number(row), row.name_ko, row.name_en, row.category,
      row.subcategory, row.desc, useCases.get(row.id)].join(" ")),
  }));
  function render() {
    const terms = normalize(query.value.trim()).split(/\s+/);
    const matches = entries.filter(({ row, text }) =>
      (!category.value || row.category_slug === category.value) &&
      terms.every((term) => text.includes(term)));
    cards.replaceChildren(...matches.map(({ row }) => makeCard(row)));
    status.textContent = matches.length ? `${matches.length}종` : "검색 결과가 없습니다.";
  }

  query.value = new URLSearchParams(location.search).get("q") ?? "";
  query.addEventListener("input", render);
  category.addEventListener("change", render);
  form.addEventListener("submit", (event) => event.preventDefault());
  render();
}

loadCatalog().catch(() => {
  status.textContent = "카드 목록을 불러오지 못했습니다. 웹 주소로 열거나 저장소의 CSV 목록을 이용하세요.";
});
