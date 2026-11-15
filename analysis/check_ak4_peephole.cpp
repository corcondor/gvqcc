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
};

int pq(const std::string& s) {
    return (s.size() >= 2 && s[0] == 'q') ? std::stoi(s.substr(1)) : -1;
}

int main() {
    int tot_ccx = 0, tot_cancels = 0, tot_merges = 0;
    for (int k = 0; k < 15; k++) {
        std::ifstream fin("/home/shibahara/gvqcc_work/ak" + std::to_string(k) + ".kmx");
        std::string line;
        std::vector<Gate> gates;
        while (std::getline(fin, line)) {
            if (line.empty()) continue;
            std::istringstream iss(line);
            Gate g;
            iss >> g.op;
            if (g.op == "REGISTER" || g.op == "APPEND_TO_REGISTER" || g.op == "INFO_TAG") continue;
            std::string tok;
            while (iss >> tok) {
                int qid = pq(tok);
                if (qid >= 0 && g.nq < 3) g.q[g.nq++] = qid;
            }
            gates.push_back(g);
        }
        int ccx_tot = 0, cancels = 0, merges = 0;
        for (size_t i = 0; i < gates.size(); i++) {
            if (gates[i].op != "CCX") continue;
            ccx_tot++;
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
        std::cout << "ak" << k << ": ccx=" << ccx_tot << ", cancels=" << cancels << ", merges=" << merges << "\n";
        tot_ccx += ccx_tot; tot_cancels += cancels; tot_merges += merges;
    }
    std::cout << "TOTAL: ccx=" << tot_ccx << ", cancels=" << tot_cancels << ", merges=" << tot_merges << "\n";
    return 0;
}
