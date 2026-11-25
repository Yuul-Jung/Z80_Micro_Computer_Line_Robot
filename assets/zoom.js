/* 그림 확대 보기 — 회로도·도면을 전체 화면에서 확대/이동
 * - 그림 클릭(또는 Enter/Space) → 보기 창 열기
 * - 마우스 휠·버튼·키보드(+ − 0)로 확대/축소, 끌어서 이동, 두 손가락 확대
 * - Esc 또는 닫기 버튼으로 닫고, 원래 그림으로 초점 복귀
 * 외부 라이브러리 없이 동작하며, JavaScript가 꺼져 있어도 본문 그림은 그대로 보인다.
 */
(function () {
  'use strict';
  var MIN = 0.2, MAX = 12;
  var box, stage, img, label, lastFocus;
  var s = 1, x = 0, y = 0, fit = 1;
  var pointers = new Map(), pinchDist = 0, pinchScale = 1, dragStart = null;

  function build() {
    box = document.createElement('div');
    box.className = 'zv';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', '그림 확대 보기');
    box.hidden = true;
    box.innerHTML =
      '<div class="zv-bar">' +
      '<span class="zv-title" id="zv-title"></span>' +
      '<button type="button" data-a="out" aria-label="축소">−</button>' +
      '<span class="zv-pct" aria-live="polite">100%</span>' +
      '<button type="button" data-a="in" aria-label="확대">+</button>' +
      '<button type="button" data-a="fit" aria-label="화면에 맞추기">맞춤</button>' +
      '<button type="button" data-a="one" aria-label="원본 크기">1:1</button>' +
      '<a class="zv-orig" target="_blank" rel="noopener">원본 파일</a>' +
      '<button type="button" data-a="close" class="zv-close" aria-label="닫기">✕</button>' +
      '</div><div class="zv-stage"><img alt=""></div>' +
      '<p class="zv-help">휠·＋/− 확대 · 끌어서 이동 · 0 맞춤 · Esc 닫기</p>';
    document.body.appendChild(box);
    stage = box.querySelector('.zv-stage');
    img = stage.querySelector('img');
    label = box.querySelector('.zv-pct');

    box.querySelector('.zv-bar').addEventListener('click', function (e) {
      var a = e.target.getAttribute && e.target.getAttribute('data-a');
      if (!a) return;
      var r = stage.getBoundingClientRect();
      if (a === 'in') zoomAt(s * 1.4, r.width / 2, r.height / 2);
      if (a === 'out') zoomAt(s / 1.4, r.width / 2, r.height / 2);
      if (a === 'fit') fitView();
      if (a === 'one') zoomAt(1, r.width / 2, r.height / 2);
      if (a === 'close') close();
    });
    stage.addEventListener('wheel', function (e) {
      e.preventDefault();
      var r = stage.getBoundingClientRect();
      zoomAt(s * (e.deltaY < 0 ? 1.15 : 1 / 1.15), e.clientX - r.left, e.clientY - r.top);
    }, { passive: false });
    stage.addEventListener('dblclick', function (e) {
      var r = stage.getBoundingClientRect();
      zoomAt(s < fit * 1.5 ? fit * 3 : fit, e.clientX - r.left, e.clientY - r.top);
    });
    stage.addEventListener('pointerdown', down);
    stage.addEventListener('pointermove', move);
    stage.addEventListener('pointerup', up);
    stage.addEventListener('pointercancel', up);
    box.addEventListener('keydown', key);
    window.addEventListener('resize', function () { if (!box.hidden) fitView(); });
  }

  function apply() {
    img.style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + s + ')';
    label.textContent = Math.round(s * 100) + '%';
  }
  function zoomAt(ns, cx, cy) {
    ns = Math.max(MIN * fit, Math.min(MAX, ns));
    x = cx - (cx - x) * (ns / s);
    y = cy - (cy - y) * (ns / s);
    s = ns; apply();
  }
  function fitView() {
    var r = stage.getBoundingClientRect();
    var w = img.naturalWidth || 1, h = img.naturalHeight || 1;
    fit = Math.min(r.width / w, r.height / h, 1) * 0.96;
    s = fit; x = (r.width - w * s) / 2; y = (r.height - h * s) / 2; apply();
  }
  function down(e) {
    stage.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 1) dragStart = { px: e.clientX, py: e.clientY, x: x, y: y };
    if (pointers.size === 2) {
      var p = Array.from(pointers.values());
      pinchDist = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y); pinchScale = s;
    }
  }
  function move(e) {
    if (!pointers.has(e.pointerId)) return;
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 2 && pinchDist) {
      var p = Array.from(pointers.values()), r = stage.getBoundingClientRect();
      var d = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y);
      zoomAt(pinchScale * d / pinchDist, (p[0].x + p[1].x) / 2 - r.left, (p[0].y + p[1].y) / 2 - r.top);
    } else if (dragStart) {
      x = dragStart.x + e.clientX - dragStart.px; y = dragStart.y + e.clientY - dragStart.py; apply();
    }
  }
  function up(e) {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinchDist = 0;
    if (pointers.size === 1) {
      var p = Array.from(pointers.values())[0];
      dragStart = { px: p.x, py: p.y, x: x, y: y };
    } else if (!pointers.size) dragStart = null;
  }
  function key(e) {
    var r = stage.getBoundingClientRect(), step = 60;
    if (e.key === 'Escape') { e.preventDefault(); close(); }
    else if (e.key === '+' || e.key === '=') zoomAt(s * 1.4, r.width / 2, r.height / 2);
    else if (e.key === '-') zoomAt(s / 1.4, r.width / 2, r.height / 2);
    else if (e.key === '0') fitView();
    else if (e.key === 'ArrowLeft') { x += step; apply(); }
    else if (e.key === 'ArrowRight') { x -= step; apply(); }
    else if (e.key === 'ArrowUp') { y += step; apply(); }
    else if (e.key === 'ArrowDown') { y -= step; apply(); }
    else if (e.key === 'Tab') {            // 보기 창 안에서만 초점 순환
      var f = box.querySelectorAll('button,a[href]');
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  }
  function open(src, title) {
    if (!box) build();
    lastFocus = document.activeElement;
    box.querySelector('.zv-title').textContent = title || '';
    box.querySelector('.zv-orig').href = src;
    box.hidden = false;
    document.documentElement.classList.add('zv-lock');
    img.onload = fitView;
    img.alt = title || '확대한 그림';
    img.src = src;
    if (img.complete) fitView();
    box.querySelector('.zv-close').focus();
  }
  function close() {
    box.hidden = true;
    document.documentElement.classList.remove('zv-lock');
    pointers.clear();
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function init() {
    var targets = document.querySelectorAll('main figure img');
    targets.forEach(function (im) {
      var fig = im.closest('figure');
      var cap = fig && fig.querySelector('figcaption');
      var title = (cap ? cap.textContent : '').trim();
      if (!title) {                      // 캡션이 없으면 절 제목 + 같은 표의 도면 정보로 이름 붙이기
        var sec = im.closest('section'), h = sec && sec.querySelector('h2');
        var head = h ? h.textContent.replace(/^\s*\d+/, '').trim() : '';
        var tbl = im.closest('table'), extra = '';
        if (tbl) {
          var cells = Array.from(tbl.querySelectorAll('td')).map(function (td) { return td.textContent.trim(); });
          var i = cells.indexOf('도면번호');
          if (i >= 0 && cells[i + 1]) extra = '도면 ' + cells[i + 1];
          var j = cells.indexOf('과제명');
          if (j >= 0 && cells[j + 1]) extra = cells[j + 1] + (extra ? ' · ' + extra : '');
        }
        title = [head, extra].filter(Boolean).join(' — ') || '본문 그림';
      }
      fig.classList.add('zoomable');
      im.setAttribute('tabindex', '0');
      im.setAttribute('role', 'button');
      im.setAttribute('aria-label', '그림 확대: ' + (title || '본문 그림'));
      function go(e) {
        e.preventDefault();
        var link = im.closest('a');
        open(link ? link.getAttribute('href') : im.getAttribute('src'), title);
      }
      im.addEventListener('click', go);
      im.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') go(e); });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
