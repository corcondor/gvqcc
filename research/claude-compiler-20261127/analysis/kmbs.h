// Streaming KMB v2 reader for the 617 MB public DQI (low RAM: ~40 MB).
// Nine file handles, one per section, each with its own 1 MB buffer.
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
#include <unordered_map>
#include <unordered_set>
#include <cinttypes>

#ifdef _WIN32
#define FSEEK64(f,o,w) _fseeki64(f,(long long)(o),w)
#else
#define FSEEK64(f,o,w) fseeko(f,(off_t)(o),w)
#endif
typedef uint64_t u64; typedef uint32_t u32; typedef uint16_t u16; typedef uint8_t u8; typedef int64_t i64;

struct KHeader {
  u32 version, nq, nb, nreg;
  u64 nops, ntof, n2, n1, nbitout, ncond;  // from header words (see notes)
  u64 h9[9];
};

struct Stream {
  FILE* f = nullptr; std::vector<u8> buf; size_t pos = 0, len = 0; u64 remaining = 0;
  void open(const char* path, u64 off, u64 size, size_t bufsz = 1 << 20) {
    f = fopen(path, "rb"); if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(2); }
    FSEEK64(f, off, SEEK_SET); remaining = size; buf.resize(bufsz); pos = len = 0;
  }
  inline bool fill() {
    if (!remaining) return false;
    size_t want = (size_t)std::min<u64>(remaining, buf.size());
    size_t got = fread(buf.data(), 1, want, f);
    if (got == 0) return false;
    len = got; pos = 0; remaining -= got; return true;
  }
  inline u8 get8() { if (pos >= len && !fill()) { fprintf(stderr, "stream underflow\n"); exit(3); } return buf[pos++]; }
  inline u32 get32() {
    u32 v;
    if (pos + 4 <= len) { memcpy(&v, &buf[pos], 4); pos += 4; return v; }
    u8 b[4]; for (int i = 0; i < 4; i++) b[i] = get8(); memcpy(&v, b, 4); return v;
  }
  void close() { if (f) fclose(f); f = nullptr; }
};

struct KmbS {
  KHeader H; std::string path; u64 secoff[16] = {0}, secsz[16] = {0};
  Stream s[10];
  void parse(const char* p) {
    path = p;
    FILE* f = fopen(p, "rb"); if (!f) { fprintf(stderr, "cannot open %s\n", p); exit(2); }
    u8 head[104]; if (fread(head, 1, 104, f) != 104) exit(2);
    u32 h4[4]; memcpy(h4, head + 16, 16); memcpy(H.h9, head + 32, 72);
    H.version = h4[0]; H.nq = h4[1]; H.nb = h4[2]; H.nreg = h4[3]; H.nops = H.h9[0];
    u64 pos = 104;
    for (;;) {
      u64 ih[2]; if (fread(ih, 8, 2, f) != 2) break; pos += 16;
      if (ih[0] >= 1 && ih[0] < 16) { secoff[ih[0]] = pos; secsz[ih[0]] = ih[1]; }
      pos += ih[1]; if (FSEEK64(f, pos, SEEK_SET) != 0) break;
    }
    fclose(f);
  }
  void begin(u64 start_op = 0) {  // only start_op == 0 supported (sequential)
    for (int i = 1; i <= 9; i++) s[i].open(path.c_str(), secoff[i], secsz[i], i == 1 ? (1 << 22) : (1 << 20));
  }
  void end() { for (int i = 1; i <= 9; i++) s[i].close(); }
};

struct SOp {
  u64 i; u8 op, base, cat; u32 q[3]; u32 bit; u32 cond; bool hasbit, hascond;
};

// sequential decoder
struct SDec {
  KmbS& k; u64 i = 0;
  explicit SDec(KmbS& kk) : k(kk) { k.begin(); }
  bool next(SOp& o) {
    if (i >= k.H.nops) return false;
    u8 op = k.s[1].get8();
    o.i = i; o.op = op; o.base = op & 127; o.cat = (op >> 4) & 3;
    o.q[0] = o.q[1] = o.q[2] = 0;
    if (o.cat == 3) { o.q[0] = k.s[2].get32(); o.q[1] = k.s[3].get32(); o.q[2] = k.s[4].get32(); }
    else if (o.cat == 2) { o.q[0] = k.s[5].get32(); o.q[1] = k.s[6].get32(); }
    else if (o.cat == 1) { o.q[0] = k.s[7].get32(); }
    o.hasbit = (op & 64) != 0; o.bit = o.hasbit ? k.s[8].get32() : 0;
    o.hascond = (op & 128) != 0; o.cond = o.hascond ? k.s[9].get32() : 0;
    i++; return true;
  }
};

static const char* opname(u8 base) {
  switch (base) {
    case 0: return "NEG"; case 1: return "POP"; case 0x10: return "Z"; case 0x11: return "X"; case 0x12: return "R";
    case 0x20: return "CZ"; case 0x21: return "CX"; case 0x22: return "SWAP"; case 0x30: return "CCZ"; case 0x31: return "CCX";
    case 0x32: return "CSWAP"; case 0x40: return "BIT_STORE0"; case 0x41: return "BIT_STORE1"; case 0x42: return "BIT_INVERT";
    case 0x50: return "HMR"; default: return "?";
  }
}
