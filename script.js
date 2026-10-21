// Quit Vaping — Web-to-App Attribution & UI Script
// Automatically formats App Store Connect campaign links (pt + ct + mt=8)
// so every web & SEO guide click is tracked inside App Store Connect > Analytics > Acquisition > Campaigns.

const ASC_CONFIG = {
  appId: "6818660091",
  providerToken: "1793695638",
  defaultCampaign: "web_organic"
};

document.querySelectorAll("[data-year]").forEach((node) => {
  node.textContent = new Date().getFullYear();
});

(function enrichAppStoreCampaignLinks() {
  const params = new URLSearchParams(window.location.search);
  const utmSource = params.get("utm_source") || params.get("ref") || "";
  const utmCampaign = params.get("utm_campaign") || params.get("ct") || "";

  document.querySelectorAll('a[href*="apps.apple.com"]').forEach((link) => {
    let baseCampaign = link.getAttribute("data-campaign") || ASC_CONFIG.defaultCampaign;
    if (utmCampaign) {
      baseCampaign = `${baseCampaign}_${utmCampaign}`;
    } else if (utmSource) {
      baseCampaign = `${baseCampaign}_${utmSource}`;
    }
    // Apple ASC campaign token max length is 40 chars, alphanumeric + _ -
    const cleanCt = baseCampaign.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 40);
    const targetUrl = new URL(`https://apps.apple.com/app/apple-store/id${ASC_CONFIG.appId}`);
    targetUrl.searchParams.set("pt", ASC_CONFIG.providerToken);
    targetUrl.searchParams.set("ct", cleanCt);
    targetUrl.searchParams.set("mt", "8");
    link.href = targetUrl.toString();
  });
})();

// --- Science section: scroll reveals ---
(function initReveals() {
  const els = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    els.forEach((el) => el.classList.add("in-view"));
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("in-view");
        entry.target.dispatchEvent(new CustomEvent("revealed"));
        io.unobserve(entry.target);
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -30px 0px" }
  );
  els.forEach((el) => io.observe(el));
})();

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// --- Urge curve: a glowing "surfer" rides the craving wave ---
(function initUrgeCurve() {
  const card = document.getElementById("urge-curve");
  const path = document.getElementById("urgePath");
  const dot = document.getElementById("urgeDot");
  if (!card || !path || !dot) return;

  const steps = card.querySelectorAll(".urge-steps li");
  const len = path.getTotalLength();
  path.style.strokeDasharray = len;
  path.style.strokeDashoffset = card.classList.contains("in-view") ? 0 : len;

  const setStep = (t) => {
    const key = t < 0.38 ? "rise" : t < 0.6 ? "peak" : "pass";
    steps.forEach((li) => li.classList.toggle("active", li.dataset.step === key));
  };

  const place = (t) => {
    const p = path.getPointAtLength(t * len);
    dot.setAttribute("cx", p.x);
    dot.setAttribute("cy", p.y);
  };

  const start = () => {
    path.style.strokeDashoffset = 0;
    if (prefersReducedMotion) {
      place(0.5);
      setStep(0.5);
      return;
    }
    const DURATION = 7000; // one full ride
    const PAUSE = 1200;
    let t0 = null;
    const tick = (now) => {
      if (t0 === null) t0 = now + 2200; // wait for line draw
      const elapsed = now - t0;
      if (elapsed >= 0) {
        const cycle = elapsed % (DURATION + PAUSE);
        const raw = Math.min(cycle / DURATION, 1);
        const t = raw < 0.5 ? 2 * raw * raw : 1 - Math.pow(-2 * raw + 2, 2) / 2; // easeInOutQuad
        place(t);
        setStep(t);
      }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  if (card.classList.contains("in-view")) start();
  else card.addEventListener("revealed", start, { once: true });
})();

// --- Breathing orb: 4s inhale / 6s exhale (same "calm 4-6" rhythm as the app) ---
(function initBreathingOrb() {
  const orb = document.getElementById("orb");
  const label = document.getElementById("orbLabel");
  const count = document.getElementById("orbCount");
  const btn = document.getElementById("orbBtn");
  if (!orb || !label || !count || !btn) return;

  const PHASES = [
    { key: "inhale", text: "Inhale pure air", secs: 4 },
    { key: "exhale", text: "Release tension", secs: 6 }
  ];
  const ROUNDS = 6; // one minute
  let running = false;
  let timers = [];

  const clear = () => {
    timers.forEach(clearTimeout);
    timers.forEach(clearInterval);
    timers = [];
  };

  const stop = (finished) => {
    running = false;
    clear();
    orb.dataset.phase = "idle";
    orb.style.setProperty("--dur", "1.2s");
    label.textContent = finished ? "Craving Surfed." : "Ready";
    count.textContent = finished ? "1 minute done" : "4 · 6";
    btn.textContent = finished ? "Surf again" : "Start breathing";
  };

  const runPhase = (round, idx) => {
    if (!running) return;
    if (round >= ROUNDS) return stop(true);
    const phase = PHASES[idx];
    orb.style.setProperty("--dur", `${phase.secs}s`);
    orb.dataset.phase = phase.key;
    label.textContent = phase.text;
    let left = phase.secs;
    count.textContent = left;
    const iv = setInterval(() => {
      left -= 1;
      if (left > 0) count.textContent = left;
    }, 1000);
    timers.push(iv);
    timers.push(
      setTimeout(() => {
        clearInterval(iv);
        const next = (idx + 1) % PHASES.length;
        runPhase(next === 0 ? round + 1 : round, next);
      }, phase.secs * 1000)
    );
  };

  btn.addEventListener("click", () => {
    if (running) return stop(false);
    running = true;
    btn.textContent = "Stop";
    runPhase(0, 0);
  });
})();

// --- Count-up stats ---
(function initCountUps() {
  const card = document.getElementById("stats-card");
  if (!card) return;
  const run = () => {
    card.querySelectorAll(".count").forEach((el, i) => {
      const to = parseFloat(el.dataset.to);
      const dec = parseInt(el.dataset.dec || "0", 10);
      if (prefersReducedMotion) {
        el.textContent = to.toFixed(dec);
        return;
      }
      const DURATION = 1600;
      const delay = 250 + i * 180;
      let t0 = null;
      const tick = (now) => {
        if (t0 === null) t0 = now + delay;
        const p = Math.max(0, Math.min((now - t0) / DURATION, 1));
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = (to * eased).toFixed(dec);
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  };
  if (card.classList.contains("in-view")) run();
  else card.addEventListener("revealed", run, { once: true });
})();
