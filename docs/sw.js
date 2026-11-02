/* 奶蛙艺术圣殿 · Service Worker（v18.0.0）
   外壳 network-first + 离线回退；同源媒体 cache-first 运行时缓存（上限 240 条）。
   纯静态站点：换版本改 VERSION 即可全量失效旧缓存。 */
var VERSION = "nw-v18.0.0";
var SHELL = ["./", "./index.html", "./data/collection.json", "./manifest.webmanifest"];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(VERSION)
      .then(function (c) { return c.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.filter(function (k) { return k !== VERSION; })
          .map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;

  /* 导航：network-first，离线回退外壳 */
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req)
        .then(function (res) {
          if (res && res.status === 200) {
            var cp = res.clone();
            caches.open(VERSION).then(function (c) { c.put("./index.html", cp); });
          }
          return res;
        })
        .catch(function () { return caches.match("./index.html"); })
    );
    return;
  }

  /* 同源媒体：cache-first + 运行时缓存（只缓存 200 全量响应，防 206 视频分片污染） */
  if (/\.(png|jpe?g|webp|gif|svg|mp3|mp4|webm)$/i.test(url.pathname)) {
    e.respondWith(
      caches.match(req).then(function (hit) {
        if (hit) return hit;
        return fetch(req)
          .then(function (res) {
            if (res && res.status === 200 && res.type === "basic") {
              var cp = res.clone();
              caches.open(VERSION).then(function (c) {
                c.put(req, cp);
                c.keys().then(function (keys) {
                  if (keys.length > 240) c.delete(keys[0]);
                });
              });
            }
            return res;
          })
          .catch(function () { return hit; });
      })
    );
  }
});
