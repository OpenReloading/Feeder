// Configurator page: reads configurator/data/manifest.json (variants.py), lists the parts of the chosen options and zips
// their STL files in the browser. The key of a part is the values of the options it depends on, as in variants.key.
(() => {
  const form = document.getElementById("configurator-form");
  if (!form) return;
  const $ = (id) => document.getElementById(id);
  const DATA = "data/";
  let manifest, current;

  const choice = () => Object.fromEntries([...form.elements].filter((e) => e.name).map((e) => [e.name, e.value]));
  const key = (deps, c) => deps.map((d) => c[d]).join("/") || "*";
  const cell = (row, text) => (row.insertCell().textContent = text);
  const mb = (bytes) => (bytes < 1e6 ? `${(bytes / 1e3).toFixed(0)} kB` : `${(bytes / 1e6).toFixed(1)} MB`);

  function resolve(c) {
    const parts = {};
    for (const [name, p] of Object.entries(manifest.parts)) {
      const hash = p.files[key(p.depends, c)];
      if (hash) parts[name] = hash;
    }
    return { parts, bom: manifest.bom.rows[key(manifest.bom.depends, c)] };
  }

  const sizes = new Map();
  // HEAD per file for the listing, once per file; a server without content-length shows no size
  const size = (hash) => {
    if (!sizes.has(hash)) {
      sizes.set(hash, fetch(`${DATA}${hash}.stl`, { method: "HEAD" }).then((r) => (r.ok ? Number(r.headers.get("content-length")) || 0 : 0)));
    }
    return sizes.get(hash);
  };

  async function render() {
    const c = (current = choice());
    const { parts, bom } = resolve(c);
    const names = Object.keys(parts).sort();
    $("configurator-result").hidden = !names.length || !bom;
    if (!names.length || !bom) return;
    const bytes = await Promise.all(names.map((n) => size(parts[n])));
    if (current !== c) return; // the options changed meanwhile
    const unique = new Set(names.map((n) => parts[n]));
    const total = [...unique].reduce((sum, h) => sum + bytes[names.findIndex((n) => parts[n] === h)], 0);
    $("configurator-summary").textContent = `${names.length} files in the zip${total ? `, ${mb(total)}` : ""}.`;
    $("configurator-parts").replaceChildren(...names.map((n, i) => {
      const row = document.createElement("tr");
      cell(row, n);
      cell(row, "1");
      cell(row, bytes[i] ? mb(bytes[i]) : "");
      return row;
    }));
    $("configurator-bom").replaceChildren(...bom.map((r) => {
      const row = document.createElement("tr");
      cell(row, r.group);
      cell(row, r.part);
      cell(row, r.qty);
      cell(row, r.spec);
      if (/^https:\/\//.test(r.link || "")) {
        const a = document.createElement("a");
        a.href = r.link;
        a.textContent = " (listing)";
        row.cells[1].append(a);
      }
      return row;
    }));
    $("configurator-status").textContent = "";
  }

  const CRC = Uint32Array.from({ length: 256 }, (_, n) => {
    for (let k = 0; k < 8; k++) n = n & 1 ? 0xedb88320 ^ (n >>> 1) : n >>> 1;
    return n >>> 0;
  });
  const crc32 = (bytes) => {
    let crc = 0xffffffff;
    for (const b of bytes) crc = CRC[(crc ^ b) & 0xff] ^ (crc >>> 8);
    return (crc ^ 0xffffffff) >>> 0;
  };

  // Store-only zip (no compression, no zip64): fine for a few dozen files of a few MB. Time is fixed at 1980-01-01.
  function zip(files) {
    const chunks = [], central = [];
    let offset = 0;
    for (const { name, data } of files) {
      const nameBytes = new TextEncoder().encode(name);
      const head = (size, fields) => {
        const view = new DataView(new ArrayBuffer(size));
        fields.forEach(([at, bytes, value]) => (bytes === 4 ? view.setUint32(at, value, true) : view.setUint16(at, value, true)));
        return new Uint8Array(view.buffer);
      };
      const crc = crc32(data);
      const common = [[4, 2, 20], [6, 2, 0x0800], [8, 2, 0], [10, 2, 0], [12, 2, 0x21], [14, 4, crc], [18, 4, data.length], [22, 4, data.length], [26, 2, nameBytes.length]];
      chunks.push(head(30, [[0, 4, 0x04034b50], ...common]), nameBytes, data);
      central.push(head(46, [[0, 4, 0x02014b50], [4, 2, 20], [6, 2, 20], [8, 2, 0x0800], [10, 2, 0], [12, 2, 0], [14, 2, 0x21], [16, 4, crc],
        [20, 4, data.length], [24, 4, data.length], [28, 2, nameBytes.length], [42, 4, offset]]), nameBytes);
      offset += 30 + nameBytes.length + data.length;
    }
    const size = central.reduce((n, c) => n + c.length, 0);
    const end = new DataView(new ArrayBuffer(22));
    end.setUint32(0, 0x06054b50, true);
    end.setUint16(8, files.length, true);
    end.setUint16(10, files.length, true);
    end.setUint32(12, size, true);
    end.setUint32(16, offset, true);
    return new Blob([...chunks, ...central, end], { type: "application/zip" });
  }

  async function download() {
    const button = $("configurator-download"), status = $("configurator-status");
    const c = choice();
    const { parts } = resolve(c);
    button.disabled = true;
    try {
      const data = new Map();
      let done = 0;
      status.textContent = "Fetching files";
      await Promise.all([...new Set(Object.values(parts))].map(async (hash) => {
        const r = await fetch(`${DATA}${hash}.stl`);
        if (!r.ok) throw new Error(`${hash}.stl: ${r.status}`);
        data.set(hash, new Uint8Array(await r.arrayBuffer()));
        status.textContent = `Fetched ${++done} of ${new Set(Object.values(parts)).size} files`;
      }));
      const files = Object.keys(parts).sort().map((n) => ({ name: `${n}.stl`, data: data.get(parts[n]) }));
      const a = document.createElement("a");
      a.href = URL.createObjectURL(zip(files));
      a.download = `feeder-${Object.values(c).join("-")}.zip`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 60000);
      status.textContent = `${files.length} files zipped`;
    } catch (e) {
      status.textContent = `Download failed: ${e.message}`;
    } finally {
      button.disabled = false;
    }
  }

  async function init() {
    try {
      const r = await fetch(`${DATA}manifest.json`);
      if (!r.ok) throw new Error(String(r.status));
      manifest = await r.json();
    } catch {
      $("configurator-unavailable").hidden = false;
      form.querySelector("fieldset").disabled = true;
      return;
    }
    form.addEventListener("change", render);
    $("configurator-download").addEventListener("click", download);
    render();
  }
  init();
})();
