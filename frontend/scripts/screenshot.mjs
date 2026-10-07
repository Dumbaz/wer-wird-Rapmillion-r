// @ts-nocheck
/**
 * Visueller Smoke-Test: klickt das Quiz wie ein echter User durch
 * und legt Screenshots in /tmp/shots ab.
 *
 *   node scripts/screenshot.mjs            (Seite muss laufen: ./start.sh, Standard http://127.0.0.1:4173)
 */
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const BASE = process.env.QUIZ_URL ?? "http://127.0.0.1:4173";
const OUT = "/tmp/shots";
mkdirSync(OUT, { recursive: true });

const log = (...a) => console.log("  ", ...a);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

const errors = [];
page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
page.on("pageerror", (e) => errors.push(String(e)));
page.on("requestfailed", (r) => errors.push(`REQUEST FAILED ${r.url()}`));

let shot = 0;
const snap = async (name, target = page) => {
  const file = `${OUT}/${String(++shot).padStart(2, "0")}-${name}.png`;
  await target.screenshot({ path: file });
  log("shot:", file);
};

// ---------------------------------------------------------------- Startseite
await page.goto(BASE, { waitUntil: "networkidle" });
await page.waitForSelector(".start__title");
log("Titel:", await page.title());
await snap("start");

// Mobile-Ansicht der Startseite
const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
await mobile.goto(BASE, { waitUntil: "networkidle" });
await mobile.waitForSelector(".start__title");
await snap("start-mobile", mobile);

// ------------------------------------------------------------------- Spielen
await page.getByRole("button", { name: "Spiel starten" }).click();
await page.waitForSelector(".question__line");
log("Frage 1:", (await page.locator(".question__line").innerText()).slice(0, 60));
await snap("frage");

// Joker: Publikum
await page.getByRole("button", { name: /Publikum/ }).click();
await page.waitForSelector(".answer__vote-bar");
await snap("publikumsjoker");

// Joker: Fifty-Fifty
await page.getByRole("button", { name: /Fifty-Fifty/ }).click();
await page.waitForSelector(".answer--removed");
await snap("fifty-fifty");

/** Klickt die laut Publikumsjoker beste Antwort und wartet auf das Reveal. */
async function answerBest() {
  const votes = await page.locator(".answer__vote-value").allInnerTexts();
  let index = 0;
  if (votes.length) {
    const nums = votes.map((v) => parseInt(v, 10));
    index = nums.indexOf(Math.max(...nums));
  }
  const buttons = page.locator(".answer:not(.answer--removed)");
  await buttons.nth(Math.min(index, (await buttons.count()) - 1)).click();
  try {
    await page.waitForSelector(".suspense");
    await page.waitForSelector(".reveal", { timeout: 8000 });
  } catch (err) {
    await snap("FEHLER-kein-reveal");
    const banner = await page.locator(".banner").innerText().catch(() => "(kein Banner)");
    log("!! Reveal blieb aus. Banner:", banner);
    log("!! Phase-DOM:", await page.locator(".stage").innerText().catch(() => "?"));
    throw err;
  }
}

await answerBest();
await page.waitForTimeout(600);
const correct = (await page.locator(".reveal--correct").count()) > 0;
log("Antwort korrekt:", correct);
log("Reveal:", (await page.locator(".reveal__artist").innerText()));

// Cover wirklich geladen?
const coverOk = await page.locator(".reveal__cover").evaluate(
  (img) => img.complete && img.naturalWidth > 0,
);
log("Cover geladen:", coverOk, "| src:", await page.locator(".reveal__cover").getAttribute("src"));
if (!coverOk) errors.push("Albumcover wurde nicht geladen");
await snap(correct ? "reveal-richtig" : "reveal-falsch");
await snap("reveal-mobile-check", page);

// --------------------------------------------- Ein paar Stufen weiter spielen
if (correct) {
  for (let i = 0; i < 4; i += 1) {
    await page.getByRole("button", { name: /Weiter zur nächsten Stufe|Ergebnis ansehen/ }).click();
    await page.waitForTimeout(300);
    if ((await page.locator(".question__line").count()) === 0) break;
    await answerBest();
    await page.waitForTimeout(400);
    if ((await page.locator(".reveal--wrong").count()) > 0) break;
  }
  const level = await page.locator(".ladder__step--active .ladder__prize").innerText().catch(() => "-");
  log("Aktuelle Stufe-Preisgeld:", level);
  await snap("spaeter-im-spiel");
}

// ------------------------------------------------------------------- Game Over
const cont = page.getByRole("button", { name: /Weiter zur nächsten Stufe|Ergebnis ansehen/ });
if (await cont.count()) {
  await cont.click();
  await page.waitForTimeout(400);
}
const cashOut = page.getByRole("button", { name: "Aussteigen" });
if (await cashOut.count()) {
  await cashOut.click();
  await page.waitForSelector(".gameover");
  log("Endstand:", await page.locator(".gameover__headline").innerText(), await page.locator(".gameover__prize").innerText());
} else if (await page.locator(".gameover").count()) {
  log("Endstand:", await page.locator(".gameover__headline").innerText());
}
await page.waitForTimeout(300);
await snap("gameover");

// Mobile-Ansicht mitten im Spiel
await mobile.getByRole("button", { name: "Spiel starten" }).click();
await mobile.waitForSelector(".question__line");
await snap("frage-mobile", mobile);

// -------------------------------------- Falsche Antwort: Cover muss trotzdem da sein
const loser = await browser.newPage({ viewport: { width: 1280, height: 900 } });
loser.on("pageerror", (e) => errors.push(String(e)));
await loser.goto(BASE, { waitUntil: "networkidle" });
await loser.getByRole("button", { name: "Spiel starten" }).click();
await loser.waitForSelector(".question__line");
// Publikumsjoker nutzen, um bewusst die schlechteste Antwort zu wählen
await loser.getByRole("button", { name: /Publikum/ }).click();
await loser.waitForSelector(".answer__vote-bar");
{
  const nums = (await loser.locator(".answer__vote-value").allInnerTexts()).map((v) => parseInt(v, 10));
  const worst = nums.indexOf(Math.min(...nums));
  await loser.locator(".answer").nth(worst).click();
  await loser.waitForSelector(".reveal", { timeout: 8000 });
  const isWrong = (await loser.locator(".reveal--wrong").count()) > 0;
  const coverVisible = await loser.locator(".reveal__cover").evaluate(
    (img) => img.complete && img.naturalWidth > 0,
  );
  log("Falsche Antwort -> Reveal sichtbar:", isWrong, "| Cover geladen:", coverVisible);
  if (!coverVisible) errors.push("Cover fehlt nach falscher Antwort");
  await snap("reveal-falsch", loser);

  await loser.getByRole("button", { name: /Ergebnis ansehen/ }).click();
  await loser.waitForSelector(".gameover");
  log("Endstand (verloren):", await loser.locator(".gameover__headline").innerText());
  await snap("gameover-verloren", loser);
}

await browser.close();

console.log(errors.length ? `\nFEHLER (${errors.length}):` : "\nKeine Konsolen-/Netzwerkfehler.");
errors.forEach((e) => console.log("  !", e));
process.exit(errors.length ? 1 : 0);
