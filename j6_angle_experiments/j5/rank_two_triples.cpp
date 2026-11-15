#include <array>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

using Row = std::array<uint16_t, 76>;

int main(int argc, char **argv) {
    if (argc != 2 && argc != 3) return 2;
    const bool quads = argc == 3;
    std::ifstream in(argv[1], std::ios::binary);
    if (!in) return 2;
    uint32_t count;
    int segment = 0;
    uint64_t total = 0;
    while (in.read(reinterpret_cast<char*>(&count), sizeof(count))) {
        std::vector<Row> rows(count);
        if (!in.read(reinterpret_cast<char*>(rows.data()), count*sizeof(Row)))
            throw std::runtime_error("incomplete segment");
        for (uint32_t i=0; i<count; ++i)
            for (uint32_t j=0; j<i; ++j) {
                Row pair;
                for (size_t c=0; c<pair.size(); ++c) pair[c]=rows[i][c]^rows[j][c];
                for (uint32_t k=0; k<j; ++k) {
                    if (quads) {
                        Row triple;
                        for (size_t c=0; c<triple.size(); ++c) triple[c]=pair[c]^rows[k][c];
                        for (uint32_t h=0; h<k; ++h) {
                            ++total;
                            uint16_t a=0, b=0;
                            bool pass=true;
                            for (size_t c=0; c<triple.size(); ++c) {
                                uint16_t x=triple[c]^rows[h][c];
                                if (!x || x==a || x==b || x==(a^b)) continue;
                                if (!a) a=x;
                                else if (!b) b=x;
                                else { pass=false; break; }
                            }
                            if (pass) std::cout << segment << " " << h << " " << k << " " << j << " " << i << "\n";
                        }
                        continue;
                    }
                    ++total;
                    uint16_t a=0, b=0;
                    bool pass=true;
                    for (size_t c=0; c<pair.size(); ++c) {
                        uint16_t x=pair[c]^rows[k][c];
                        if (!x || x==a || x==b || x==(a^b)) continue;
                        if (!a) a=x;
                        else if (!b) b=x;
                        else {pass=false;break;}
                    }
                    if (pass) std::cout << segment << " " << k << " " << j << " " << i << "\n";
                }
            }
        ++segment;
    }
    std::cerr << "tested " << total << (quads ? " quadruples over " : " triples over ") << segment << " segments\n";
}
