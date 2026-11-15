#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>

struct Gate {
    std::string op;
    int q[3] = {-1,-1,-1};
    int nq = 0;
};

int pq(const std::string& s) {
    return (s.size() >= 2 && s[0] == 'q') ? std::stoi(s.substr(1)) : -1;
}

int main() {
    std::ifstream fin("/home/shibahara/gvqcc_work/invsqrt.kmx");
    std::string line;
    std::unordered_map<std::string, int> counts;
    std::vector<Gate> gates;
    while (std::getline(fin, line)) {
        if (line.empty()) continue;
        std::istringstream iss(line);
        Gate g;
        iss >> g.op;
        if (g.op == "REGISTER" || g.op == "APPEND_TO_REGISTER" || g.op == "INFO_TAG") continue;
        counts[g.op]++;
        std::string tok;
        while (iss >> tok) {
            int qid = pq(tok);
            if (qid >= 0 && g.nq < 3) g.q[g.nq++] = qid;
        }
        gates.push_back(g);
    }
    for (auto& kv : counts) std::cout << "  " << kv.first << ": " << kv.second << "\n";
    int cancels = 0, merges = 0;
    for (size_t i = 0; i < gates.size(); i++) {
        if (gates[i].op != "CCX") continue;
        int c0 = std::min(gates[i].q[0], gates[i].q[1]);
        int c1 = std::max(gates[i].q[0], gates[i].q[1]);
        int t = gates[i].q[2];
        bool bt = false;
        for (int j = (int)i - 1; j >= 0 && (int)i - j <= 256; j--) {
            const Gate& pj = gates[j];
            if (pj.op == "R" || pj.op == "HMR" || pj.op == "PUSH_CONDITION" || pj.op == "POP_CONDITION") break;
            if (pj.op == "CCX") {
                int pc0 = std::min(pj.q[0], pj.q[1]);
                int pc1 = std::max(pj.q[0], pj.q[1]);
                if (pc0 == c0 && pc1 == c1) {
                    if (pj.q[2] == t && !bt) { cancels++; break; }
                    if (pj.q[2] != t && !bt) { merges++; break; }
                }
            }
            bool mod_c = false;
            if (pj.op == "X" && (pj.q[0] == c0 || pj.q[0] == c1)) mod_c = true;
            if (pj.op == "CX" && (pj.q[1] == c0 || pj.q[1] == c1)) mod_c = true;
            if (pj.op == "CCX" && (pj.q[2] == c0 || pj.q[2] == c1)) mod_c = true;
            if (pj.op == "SWAP" && (pj.q[0] == c0 || pj.q[0] == c1 || pj.q[1] == c0 || pj.q[1] == c1)) mod_c = true;
            if (mod_c) break;
            for (int m = 0; m < pj.nq; m++) if (pj.q[m] == t) bt = true;
        }
    }
    std::cout << "invsqrt CCX cancels=" << cancels << ", merges=" << merges << "\n";
    return 0;
}
