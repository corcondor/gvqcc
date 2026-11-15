#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>

struct Gate {
    std::string op;
    int q[3] = {-1,-1,-1};
    int nq = 0;
    int cond = -1;
    std::string raw;
};

int pq(const std::string& s) {
    return (s.size() >= 2 && s[0] == 'q') ? std::stoi(s.substr(1)) : -1;
}

int main() {
    // Stream baseline_dqi.kmx in blocks separated by R/HMR/PUSH_CONDITION/POP_CONDITION
    // Within each block, find CCX pairs with same (c0, c1) where commuting them together is valid!
    std::ifstream fin("/home/shibahara/gvqcc_work/baseline_dqi.kmx");
    std::string line;
    std::vector<Gate> blk;
    long long total_ccx = 0, total_cancels = 0, total_merges = 0;

    auto process_blk = [&]() {
        // For each CCX at i, look backward in blk for another CCX at j with same (c0, c1)
        // A gate g at m in (j+1 .. i-1) blocks moving CCX_i left to j+1 ONLY if:
        //   g writes to c0, c1, or t_i, OR g reads t_i (actually CX(t_i, x) can stay or move? Conservative: g touches t_i!)
        for (int i = 0; i < (int)blk.size(); i++) {
            if (blk[i].op != "CCX") continue;
            total_ccx++;
            int c0 = std::min(blk[i].q[0], blk[i].q[1]);
            int c1 = std::max(blk[i].q[0], blk[i].q[1]);
            int t = blk[i].q[2];
            for (int j = i - 1; j >= 0 && i - j <= 1024; j--) {
                const Gate& pj = blk[j];
                if (pj.op == "CCX" && pj.cond == blk[i].cond) {
                    int pc0 = std::min(pj.q[0], pj.q[1]);
                    int pc1 = std::max(pj.q[0], pj.q[1]);
                    if (pc0 == c0 && pc1 == c1) {
                        if (pj.q[2] == t) {
                            total_cancels++;
                            blk[j].op = "NOP";
                            blk[i].op = "NOP";
                            break;
                        } else {
                            total_merges++;
                            blk[j].op = "MERGED"; // mark so we don't double-count
                            blk[i].op = "NOP";
                            break;
                        }
                    }
                }
                // Check if pj blocks moving CCX(c0, c1, t) left past pj:
                // 1) pj writes to c0 or c1
                bool blocks = false;
                if (pj.op == "X" && (pj.q[0] == c0 || pj.q[0] == c1)) blocks = true;
                else if (pj.op == "CX" && (pj.q[1] == c0 || pj.q[1] == c1)) blocks = true;
                else if (pj.op == "CCX" && (pj.q[2] == c0 || pj.q[2] == c1)) blocks = true;
                else if (pj.op == "SWAP" && (pj.q[0] == c0 || pj.q[0] == c1 || pj.q[1] == c0 || pj.q[1] == c1)) blocks = true;
                else if (pj.op == "CSWAP" && (pj.q[1] == c0 || pj.q[1] == c1 || pj.q[2] == c0 || pj.q[2] == c1)) blocks = true;
                else if (pj.op == "MERGED") blocks = true;
                // 2) pj touches t (read or write) -> wait: Z/CZ/CCZ on t? Z/CZ/CCZ doesn't commute with CCX(..., t)!
                if (!blocks) {
                    for (int m = 0; m < pj.nq; m++) {
                        if (pj.q[m] == t) { blocks = true; break; }
                    }
                }
                if (blocks) break;
            }
        }
        blk.clear();
    };

    while (std::getline(fin, line)) {
        if (line.empty()) continue;
        std::istringstream iss(line);
        Gate g;
        iss >> g.op;
        if (g.op == "REGISTER" || g.op == "APPEND_TO_REGISTER" || g.op == "INFO_TAG" || g.op == "DEBUG_PRINT") continue;
        if (g.op == "R" || g.op == "HMR" || g.op == "PUSH_CONDITION" || g.op == "POP_CONDITION") {
            process_blk();
            continue;
        }
        std::string tok;
        bool next_if = false;
        while (iss >> tok) {
            if (tok == "if") { next_if = true; continue; }
            if (next_if) { g.cond = std::stoi(tok.substr(1)); next_if = false; continue; }
            int qid = pq(tok);
            if (qid >= 0 && g.nq < 3) g.q[g.nq++] = qid;
        }
        blk.push_back(std::move(g));
    }
    process_blk();
    std::cout << "total_ccx=" << total_ccx << ", cancels=" << total_cancels << " (-" << 2*total_cancels
              << "), merges=" << total_merges << " (-" << total_merges << "), total_saved=" << (2*total_cancels + total_merges) << "\n";
    return 0;
}
