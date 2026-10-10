(function () {
  "use strict";
  var root = document.documentElement;

  /* ---------- language switch ---------- */
  function currentLang() { return root.classList.contains("lang-zh") ? "zh" : "en"; }
  function showLang() {
    var lang = currentLang();
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.lang === lang ? "true" : "false");
    });
  }
  document.querySelectorAll(".lang button").forEach(function (b) {
    b.addEventListener("click", function () {
      var zh = b.dataset.lang === "zh";
      root.classList.toggle("lang-zh", zh);
      root.lang = zh ? "zh-CN" : "en";
      try { localStorage.setItem("lang", zh ? "zh" : "en"); } catch (e) {}
      showLang();
    });
  });
  showLang();

  /* ---------- home: a random featured photo on each visit ---------- */
  var heroImg = document.getElementById("hero-img");
  var captions = Array.prototype.slice.call(document.querySelectorAll(".hero-caption"));
  var heroIndex = -1;
  function showHero(i) {
    var c = captions[i];
    heroIndex = i;
    captions.forEach(function (other) { other.hidden = other !== c; });
    heroImg.srcset = c.dataset.srcset;
    heroImg.src = c.dataset.src;
    heroImg.alt = c.dataset.alt;
    document.getElementById("hero-link").href = c.dataset.href;
  }
  if (heroImg && captions.length) {
    showHero(Math.floor(Math.random() * captions.length));
    document.querySelectorAll(".hero-shuffle").forEach(function (b) {
      b.addEventListener("click", function () {
        var next = heroIndex;
        while (next === heroIndex) { next = Math.floor(Math.random() * captions.length); }
        showHero(next);
      });
    });
  }

  /* ---------- all photos: filter by series and place ---------- */
  var grid = document.getElementById("grid");
  if (grid) {
    var tiles = Array.prototype.slice.call(grid.querySelectorAll(".tile"));
    var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
    var state = { series: "", place: "" };

    var readHash = function () {
      state = { series: "", place: "" };
      location.hash.replace(/^#/, "").split("&").forEach(function (pair) {
        var kv = pair.split("=");
        if (kv[0] in state && kv[1]) { state[kv[0]] = decodeURIComponent(kv[1]); }
      });
    };
    var apply = function () {
      var shown = 0;
      tiles.forEach(function (tile) {
        var ok = (!state.series || tile.dataset.series === state.series) &&
                 (!state.place || tile.dataset.place === state.place);
        tile.hidden = !ok;
        if (ok) { shown += 1; }
      });
      chips.forEach(function (chip) {
        chip.setAttribute("aria-pressed", state[chip.dataset.group] === chip.dataset.value ? "true" : "false");
      });
      document.getElementById("shown").textContent = shown;
      document.getElementById("empty").hidden = shown !== 0;
    };
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        state[chip.dataset.group] = chip.dataset.value;
        var parts = [];
        if (state.series) { parts.push("series=" + encodeURIComponent(state.series)); }
        if (state.place) { parts.push("place=" + encodeURIComponent(state.place)); }
        history.replaceState(null, "", parts.length ? "#" + parts.join("&") : location.pathname + location.search);
        apply();
      });
    });
    window.addEventListener("hashchange", function () { readHash(); apply(); });
    readHash();
    apply();
  }

  /* ---------- single photo: arrow keys ---------- */
  var prev = document.getElementById("prev");
  var next = document.getElementById("next");
  if (prev || next) {
    document.addEventListener("keydown", function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) { return; }
      if (e.key === "ArrowLeft" && prev) { location.href = prev.href; }
      if (e.key === "ArrowRight" && next) { location.href = next.href; }
    });
  }
})();
