/**
 * Scroll-spy, forma yuklanishi, xabar yopish, yuqoriga qaytish.
 */
(function () {
  function prefersReducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function throttle(fn, wait) {
    var t = null;
    return function () {
      var ctx = this;
      var args = arguments;
      if (t) return;
      t = window.setTimeout(function () {
        t = null;
        fn.apply(ctx, args);
      }, wait);
    };
  }

  function navScrollSpy() {
    var nav = document.querySelector(".nav-flow");
    if (!nav) return;
    var links = [].slice.call(nav.querySelectorAll('a[href^="#"]'));
    var ids = links
      .map(function (a) {
        return (a.getAttribute("href") || "").slice(1);
      })
      .filter(Boolean);

    function activeId() {
      var bar = document.querySelector(".top-flow");
      var y = (bar ? bar.offsetHeight : 96) + 12;
      var current = ids[0] || "";
      for (var i = 0; i < ids.length; i++) {
        var el = document.getElementById(ids[i]);
        if (!el) continue;
        var top = el.getBoundingClientRect().top;
        if (top <= y) current = ids[i];
      }
      return current;
    }

    function paint() {
      var id = activeId();
      links.forEach(function (a) {
        var h = (a.getAttribute("href") || "").slice(1);
        var on = h === id;
        a.classList.toggle("is-active", on);
        if (on) a.setAttribute("aria-current", "location");
        else a.removeAttribute("aria-current");
      });
    }

    window.addEventListener("scroll", throttle(paint, 80), { passive: true });
    window.addEventListener("resize", throttle(paint, 120));
    paint();
  }

  function formBusyState() {
    document.querySelectorAll("form.grid-form").forEach(function (form) {
      form.addEventListener("submit", function () {
        var btn = form.querySelector('button[type="submit"]');
        if (!btn || btn.disabled) return;
        btn.disabled = true;
        btn.classList.add("is-loading");
        btn.setAttribute("aria-busy", "true");
        var label = (btn.textContent || "").trim();
        btn.setAttribute("data-prev-label", label);
        btn.innerHTML =
          '<span class="btn-spinner" aria-hidden="true"></span><span class="btn-label">' +
          label +
          "</span>";
      });
    });
  }

  function dismissMessages() {
    var box = document.querySelector(".messages");
    if (!box) return;
    [].slice.call(box.querySelectorAll(".msg")).forEach(function (msg) {
      if (msg.querySelector(".msg-dismiss")) return;
      var b = document.createElement("button");
      b.type = "button";
      b.className = "msg-dismiss";
      b.setAttribute("aria-label", "Yopish");
      b.textContent = "×";
      msg.appendChild(b);
      b.addEventListener("click", function () {
        msg.style.opacity = "0";
        msg.style.transform = "translateY(-6px)";
        window.setTimeout(function () {
          msg.remove();
          if (!box.querySelector(".msg")) box.remove();
        }, prefersReducedMotion() ? 0 : 200);
      });
    });
  }

  function backToTop() {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-back-top";
    btn.setAttribute("aria-label", "Yuqoriga");
    btn.innerHTML =
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>';
    document.body.appendChild(btn);

    function toggle() {
      btn.classList.toggle("is-visible", window.scrollY > 420);
    }

    window.addEventListener("scroll", throttle(toggle, 150), { passive: true });
    toggle();

    btn.addEventListener("click", function () {
      window.scrollTo({
        top: 0,
        behavior: prefersReducedMotion() ? "auto" : "smooth",
      });
    });
  }

  function main() {
    navScrollSpy();
    formBusyState();
    dismissMessages();
    backToTop();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    main();
  }
})();
