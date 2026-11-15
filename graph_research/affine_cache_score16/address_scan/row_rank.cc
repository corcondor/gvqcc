// Rank proxy for moves preserving each local chemistry address tag.
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

constexpr int bits = 600;
constexpr int blocks = 76;
using Column = std::array<unsigned, bits>;
using Permutation = std::array<int,16>;

struct Basis {
  std::array<unsigned,15> pivots{};
  int rank=0;

  unsigned remainder(unsigned word) const {
    while (word) {
      const unsigned h=31-__builtin_clz(word);
      if (pivots[h]==0) break;
      word ^= pivots[h];
    }
    return word;
  }
  void insert(unsigned word) {
    word=remainder(word);
    if (word) {
      pivots[31-__builtin_clz(word)]=word;
      ++rank;
    }
  }
};

unsigned change(unsigned original, const Permutation &p) {
  const unsigned source=original << 1;
  const unsigned base=(source >> p[0]) & 1;
  unsigned out=0;
  for (int i=1;i<16;++i) {
    out |= (((source >> p[i]) & 1) ^ base) << (i-1);
  }
  return out;
}

std::array<int,2> objective(const std::array<Column,blocks> &data) {
  std::array<int,2> value{};
  for (int b=0;b<bits;++b) {
    Basis basis;
    for (const auto &col:data) basis.insert(col[b]);
    value[0]+=(basis.rank+1)/2;
    value[1]+=basis.rank;
  }
  return value;
}

int main(int argc,char **argv) {
  if (argc!=3) return 1;
  std::ifstream in(argv[1]);
  int num_options,nmoves;
  in>>num_options>>nmoves;
  std::vector<Permutation> options(num_options);
  for (auto &p:options) for (int &i:p) in>>i;
  std::vector<int> moves(nmoves);
  for (int &i:moves) in>>i;
  std::array<Column,blocks> data{};
  for (auto &c:data) for (auto &w:c) in>>w;
  if (!in) return 2;

  std::array<Permutation,blocks> order{};
  for (auto &p:order) std::iota(p.begin(),p.end(),0);
  const auto before=objective(data);
  int accepted=0,sweeps=0;
  std::mt19937 rng(21517);
  std::array<Basis,bits> without;

  while (sweeps<12) {
    ++sweeps;
    int changed=0;
    std::shuffle(moves.begin(),moves.end(),rng);
    for (const int block:moves) {
      for (int b=0;b<bits;++b) {
        without[b]=Basis{};
        for (int i=0;i<blocks;++i) if (i!=block) without[b].insert(data[i][b]);
      }
      std::array<int,2> best{10000,10000};
      int choice=0;
      for (int p=0;p<num_options;++p) {
        std::array<int,2> cost{};
        for (int b=0;b<bits;++b) {
          const auto &basis=without[b];
          const int full=basis.rank+(basis.remainder(change(data[block][b],options[p]))!=0);
          cost[0]+=(full+1)/2;
          cost[1]+=full;
        }
        if (cost<best) {
          best=cost;
          choice=p;
        }
      }
      if (choice) {
        const auto old=order[block];
        for (int i=0;i<16;++i) order[block][i]=old[options[choice][i]];
        for (auto &w:data[block]) w=change(w,options[choice]);
        ++accepted;
        ++changed;
      }
    }
    if (!changed) break;
  }

  const auto after=objective(data);
  std::ofstream out(argv[2]);
  out<<"{\n  \"proxy_before\": ["<<before[0]<<","<<before[1]<<"],\n"
    <<"  \"proxy_after\": ["<<after[0]<<","<<after[1]<<"],\n"
    <<"  \"accepted_transpositions\": "<<accepted<<",\n"
    <<"  \"completed_sweeps\": "<<sweeps<<",\n  \"row_map\": [\n";
  for (int i=0;i<blocks;++i) {
    out<<"    [";
    for (int j=0;j<16;++j) out<<(j?",":"")<<i*16+order[i][j];
    out<<"]"<<(i==blocks-1?"\n":",\n");
  }
  out<<"  ]\n}\n";
  std::cout<<before[0]<<" -> "<<after[0]<<", accepted "<<accepted<<" swaps\n";
}
