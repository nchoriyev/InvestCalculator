/**
 * Chart.js: kechiktirilgan render (viewport yaqinida), qorong‘i tema, reduced-motion.
 */
(function () {
  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function themeColors() {
    var dark = document.documentElement.getAttribute("data-theme") === "dark";
    return {
      grid: dark ? "rgba(148, 163, 184, 0.12)" : "rgba(15, 23, 42, 0.08)",
      tick: dark ? "#94a3b8" : "#64748b",
    };
  }

  function baseOptions(type) {
    var tc = themeColors();
    var reduced = prefersReducedMotion();
    var anim = reduced
      ? false
      : { duration: 900, easing: "easeOutQuart" };
    var legend = { labels: { color: tc.tick, font: { family: "Outfit, system-ui, sans-serif" } } };
    if (type === "doughnut" || type === "pie") {
      return { animation: anim, plugins: { legend } };
    }
    return {
      animation: anim,
      plugins: { legend },
      scales: {
        x: { ticks: { color: tc.tick, maxRotation: 0 }, grid: { color: tc.grid } },
        y: { ticks: { color: tc.tick }, grid: { color: tc.grid } },
      },
    };
  }

  function render(key, entry) {
    if (typeof Chart === "undefined") return;
    var reduced = prefersReducedMotion();
    var cfg = entry && entry.chart;
    if (!cfg || cfg.type === "none") return;
    var canvas = document.getElementById("chart-" + key);
    if (!canvas) return;
    var prev = Chart.getChart(canvas);
    if (prev) prev.destroy();

    var ds = (cfg.datasets || []).map(function (d) {
      return Object.assign({ borderWidth: 1 }, d);
    });
    var data = { labels: cfg.labels || [], datasets: ds };

    var type = cfg.type === "doughnut" ? "doughnut" : cfg.type;
    var options = Object.assign({}, baseOptions(type));
    if (type === "doughnut") {
      options.cutout = "62%";
    }
    if (type === "line") {
      options.elements = { line: { tension: reduced ? 0 : 0.35 } };
      if (data.datasets[0]) {
        data.datasets[0].fill = "start";
        data.datasets[0].backgroundColor = "rgba(2, 132, 199, 0.12)";
        data.datasets[0].borderColor = "#0284c7";
        data.datasets[0].borderWidth = 2;
      }
    }

    new Chart(canvas, { type: type, data: data, options: options });
  }

  function scheduleRender(key, entry) {
    var canvas = document.getElementById("chart-" + key);
    if (!canvas) return;
    var wrap = canvas.closest(".chart-wrap");
    var run = function () {
      render(key, entry);
      if (wrap) wrap.classList.add("chart-wrap--ready");
    };
    if (prefersReducedMotion() || !wrap || !("IntersectionObserver" in window)) {
      run();
      return;
    }
    var obs = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            obs.disconnect();
            run();
          }
        });
      },
      { root: null, rootMargin: "100px 0px 120px 0px", threshold: 0.01 }
    );
    obs.observe(wrap);
  }

  function destroyAllCharts() {
    if (typeof Chart === "undefined") return;
    document.querySelectorAll('canvas[id^="chart-"]').forEach(function (c) {
      var ch = Chart.getChart(c);
      if (ch) ch.destroy();
    });
    document.querySelectorAll(".chart-wrap").forEach(function (w) {
      w.classList.remove("chart-wrap--ready");
    });
  }

  function initCharts() {
    var el = document.getElementById("dashboard-results");
    if (!el || typeof Chart === "undefined") return;
    var payload = {};
    try {
      payload = JSON.parse(el.textContent);
    } catch (e) {
      return;
    }
    destroyAllCharts();
    Object.keys(payload).forEach(function (k) {
      scheduleRender(k, payload[k]);
    });
  }

  function scrollToHash() {
    var hash = window.location.hash.replace("#", "");
    if (!hash) return;
    var target = document.getElementById(hash);
    if (!target) return;
    target.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
  }

  function boot() {
    initCharts();
    scrollToHash();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    window.setTimeout(function () {
      initCharts();
    }, 0);
  });
})();
