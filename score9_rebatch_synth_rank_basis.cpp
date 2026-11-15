// Exact output-basis search for the 15 x 76 cross-partition matrix space.
// Enumerate every nonzero left-null vector; every rank-deficient output
// combination occurs in at least one resulting output-coefficient kernel.
// No external dependencies. This audits a synthesis class, not all circuits.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <vector>

using U = uint32_t;
int high(U x) { return 31 - __builtin_clz(x); }
int main(int argc, char **argv) {
  if (argc != 3) throw std::runtime_error("input.txt output.txt");
  std::ifstream in(argv[1]);
  int nlo, nhi, no;
  in >> nlo >> nhi >> no;
  if (nlo > 20 || no > 31) throw std::runtime_error("dimension too large");
  std::vector<std::vector<U>> tensor(nlo, std::vector<U>(nhi));
  for (auto &row : tensor) for (auto &v : row) in >> v;
  if (!in) throw std::runtime_error("input incomplete");
  std::set<U> deficient{0};
  std::vector<U> contracted(nhi);
  unsigned long long nullspaces = 0, maximum_dimension = 0;
  U previous = 0;
  for (U count = 1; count < (U(1) << nlo); ++count) {
    U gray = count ^ (count >> 1), changed = gray ^ previous;
    const int row = __builtin_ctz(changed);
    previous = gray;
    for (int j = 0; j < nhi; ++j) contracted[j] ^= tensor[row][j];
    std::array<U, 32> pivots{};
    int rank = 0;
    for (auto v : contracted) {
      while (v && pivots[high(v)]) v ^= pivots[high(v)];
      if (v) { pivots[high(v)] = v; ++rank; }
    }
    int dimension = no - rank;
    if (!dimension) continue;
    ++nullspaces;
    maximum_dimension = std::max(maximum_dimension, (unsigned long long)dimension);
    if (dimension > 20) throw std::runtime_error("kernel enumeration too large");
    std::vector<U> kernel;
    for (int free = 0; free < no; ++free) if (!pivots[free]) {
      U value = U(1) << free;
      for (int p = 0; p < no; ++p)
        if (pivots[p] && __builtin_parity(value & pivots[p])) value ^= U(1) << p;
      for (U equation : contracted)
        if (__builtin_parity(value & equation)) throw std::runtime_error("bad nullspace");
      kernel.push_back(value);
    }
    std::vector<U> values{0};
    for (U v : kernel) {
      const size_t old = values.size();
      for (size_t i = 0; i < old; ++i) values.push_back(values[i] ^ v);
    }
    deficient.insert(values.begin(), values.end());
  }
  std::ofstream out(argv[2]);
  out << "# complete " << deficient.size() << " nullspaces " << nullspaces
      << " max_dimension " << maximum_dimension << "\n";
  for (U v : deficient) out << v << '\n';
  std::cout << "{\"rank_deficient_outputs\":" << deficient.size()
            << ",\"nontrivial_nullspaces\":" << nullspaces
            << ",\"maximum_kernel_dimension\":" << maximum_dimension << "}\n";
}
