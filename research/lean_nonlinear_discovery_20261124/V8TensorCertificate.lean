/-
Lean 4.35 formal certificate from real V8 k8 source KMB SHA256
227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898.
129→130 nonmonotone exact Boolean identities. This is NOT a 210T claim.
-/
import Init
namespace GVQCC.RealV8

abbrev CutInput := Fin 98 → Bool
abbrev OutputBit := Fin 35

inductive LinExpr where
 | atom (mask : Nat)
 | plus (a b : LinExpr)
 deriving Repr

def parity (mask : Nat) (x : CutInput) : Bool :=
 (List.range 98).foldl
   (fun acc i => Bool.xor acc
      (if h : i < 98 then Bool.and (Nat.testBit mask i) (x ⟨i,h⟩) else false))
   false

def LinExpr.eval : LinExpr → CutInput → Bool
 | .atom m, x => parity m x
 | .plus p q, x => Bool.xor (p.eval x) (q.eval x)

structure Term where
 a : LinExpr
 b : LinExpr
 o : Nat
 deriving Repr

def Term.eval (t : Term) (x : CutInput) (j : OutputBit) : Bool :=
 Bool.and (Bool.and (t.a.eval x) (t.b.eval x)) (Nat.testBit t.o j.val)

def evalTerms : List Term → CutInput → OutputBit → Bool
 | [], _, _ => false
 | t :: ts, x, j => Bool.xor (t.eval x j) (evalTerms ts x j)

/-- These are the EXACT factor masks recovered from public V8 k8,
    before the first HMR; no invented test terms. -/
def t0 : Term := ⟨.atom 0x2, .atom 0x1, 0x1c1070e00⟩
def t1 : Term := ⟨.atom 0x2d0c79d25475cc93b94b3ad2d, .atom 0x786c8dcb6d05bf9a463abdda, 0x26c18404⟩
def t2 : Term := ⟨.atom 0x90835754ef46ae2371a6a5b, .atom 0x2d87d3694a2c0139577b88cb0, 0x3648b0436⟩

def rest : List Term := [
  ⟨.atom 0x39c073a288ff5576cd45ae2f5, .atom 0x3dfc91547b0f9d78edbed2ada, 0x610d043e⟩,
  ⟨.atom 0x1411940004e4a51e826275835, .atom 0xdb344726c2e585e1f520b0b0, 0x2e0c6090e⟩,
  ⟨.atom 0x15506c3ed6e90a0cbec9362b1, .atom 0x31ad3f86f9831c9c9fb1bda39, 0x3c58b811e⟩,
  ⟨.atom 0x27bb7331846f731f9ab11c60a, .atom 0xe1b288f5fa3eb3c3d0dc2bc1, 0x161c70322⟩,
  ⟨.atom 0x3b5af5d3ac33777df0223a88d, .atom 0x3feaf3c6c8986a8b0e358bf7b, 0x1e0c00906⟩,
  ⟨.atom 0x29752bba958e535c709f46450, .atom 0x1ae20283104e08af5f543d8c9, 0x266cc0136⟩,
  ⟨.atom 0x123b7989a7a9544847768b8e2, .atom 0x23b2871203479b19238a8fe6e, 0x1c08b0630⟩,
  ⟨.atom 0x173f073726ef55de654b8d131, .atom 0x27f8dd015c52f769aa3db2c7b, 0x365428234⟩,
  ⟨.atom 0x1ddd48175d63665f38e370da3, .atom 0x199b61ed87b823aa4c457e9ec, 0x1200e020e⟩,
  ⟨.atom 0x35d183b82d614f840aeb097fc, .atom 0x27722be380369944b6c5b3ba4, 0x326408e28⟩,
  ⟨.atom 0x3831fd7ba4c1dbb4a34589bd9, .atom 0x219e4799a350418e43979c439, 0x1a70d8734⟩,
  ⟨.atom 0x24a515cf898e96ecac4d61a59, .atom 0x138191a73e2dc087329376e6, 0x1a6c2051a⟩,
  ⟨.atom 0x7d192648f46245049dae98b8, .atom 0x30b5695c4f8935a32c6012fe1, 0x100018d02⟩,
  ⟨.atom 0x20da66f5c12170e93c0989e9, .atom 0xa159f5cc3773f6ee461d078b, 0x1464b8a1e⟩,
  ⟨.atom 0x2c5ad050eb71629d4cead2a9d, .atom 0x3d82b80b91b9998887507ff2c, 0x227408a0c⟩,
  ⟨.atom 0x1b102f7dc05a284a7ad6bad59, .atom 0xbcaa4e544fe86ea07a2bca4, 0x242470500⟩,
  ⟨.atom 0x2d7e9da354838eb6f7387f19e, .atom 0x8d9c50af672e44a0a22e0a21, 0x65430b12⟩,
  ⟨.atom 0xcbd013f7ee0b548c7e260656, .atom 0x2c6cead988bf86524499c7398, 0x25878b28⟩,
  ⟨.atom 0xccd46e621255342ce1df40af, .atom 0x3a4bed6a60e4f7abded6a3180, 0x43cd0d38⟩,
  ⟨.atom 0x33aae45066261ece8082c1472, .atom 0xeabdb2c4e51166a8782659ef, 0x34085021c⟩,
  ⟨.atom 0x2cd2d4d23b00ce32196071a89, .atom 0x20f5be7d01d8e617247c89605, 0x143420338⟩,
  ⟨.atom 0x21cefc9d21d1b58b4cee6c371, .atom 0x1261880c0485cfaac8fbc6b4d, 0x2c54b0914⟩,
  ⟨.atom 0x12a3ccc19fc4a10e190b4ee04, .atom 0x2f416c19ce867e478756f65e7, 0x226810c0e⟩,
  ⟨.atom 0x3323d93866e5ddc0602c0441e, .atom 0x8edf7b38fddcb23a50561365, 0x1858f8d0a⟩,
  ⟨.atom 0x294f317912dd5ce43b3081378, .atom 0x8819f7c6df303e44914c279b, 0x1c08d0638⟩,
  ⟨.atom 0x372907a65e74b5d49a8c69bfc, .atom 0x3025acfd244480c2d1fbaea26, 0x3a7088528⟩,
  ⟨.atom 0x3e59d3d0d55861ecc580b5e5a, .atom 0x1d1c6138b4a18a76b5ffb4e29, 0x60868104⟩,
  ⟨.atom 0x1605711b15910af6a699cb67c, .atom 0x35f8e9374ee952a0590357b87, 0x1e0070c06⟩,
  ⟨.atom 0x2f44827fcc3ac422a3fcde6b4, .atom 0xf0b3f593f67f125d17b64c98, 0x40848f1e⟩,
  ⟨.atom 0x86f9c0bed17e9706d5646be0, .atom 0xffbfbba5af2c91f3c7efa995, 0xa54c823c⟩,
  ⟨.atom 0x69ad11291ab32d20db5d4bd1, .atom 0x18ee9b5697737fe47b77d09ab, 0x24c9032a⟩,
  ⟨.atom 0x1c165f29b6fe7a625e67813d9, .atom 0x3f9489414005b143f16e00ece, 0x1600b8318⟩,
  ⟨.atom 0x33468f11f6ee95ec8170c6890, .atom 0x4c454d390d4b82355cd7560c, 0x1a14f0706⟩,
  ⟨.atom 0x1a9897582d1f63405f03280bd, .atom 0x29a8060cef83e11f6e8499a7f, 0x227cc0512⟩,
  ⟨.atom 0x169bbcc1e65fff13834b8f90d, .atom 0x376265b37ee5a0e7b0d917038, 0x1450d8532⟩,
  ⟨.atom 0x12f4dffc0a66688cf921b069a, .atom 0x82e272e0e9bd34efd247ac05, 0x1628c8d18⟩,
  ⟨.atom 0x12361d7abc238758bd534a71d, .atom 0x1d270c7f1a9bd92ea301ad022, 0x363c99400⟩,
  ⟨.atom 0x2ff07a65c63ec884e036ae3ca, .atom 0x28b2aa12291f1e2dfe695c03d, 0x185031400⟩,
  ⟨.atom 0x72eab7324e196d520eb6fa6d, .atom 0x250f935a191bb3b1c048e0427, 0x2c1021800⟩,
  ⟨.atom 0x35c84b6dd342cf3bf8a414e05, .atom 0x1b062c43a91c244d300da01f5, 0x264c79000⟩,
  ⟨.atom 0x2dd41186a6ac196997be49b79, .atom 0x9919933adcef241182bf68c3, 0x448a1000⟩,
  ⟨.atom 0xe0bd637f2748191c6e7276c1, .atom 0x27a9e728e7b094bf3d3bd8c6b, 0xa54a8800⟩,
  ⟨.atom 0x266694bc1ed858ce9999bc24b, .atom 0x13ff8925f8a5eaf1b93410234, 0xc6831c00⟩,
  ⟨.atom 0x2cf8a530fdb08388b2c1f2fcd, .atom 0x1547220d276b287fcf1d44187, 0x2408f0000⟩,
  ⟨.atom 0xa8aab23da88e7d90845051b5, .atom 0x1333bbd62c21aab2e7f115f02, 0x3c40a0000⟩,
  ⟨.atom 0x2dba255f7560209fa021c5d77, .atom 0x3dbfc80a25ddc8f7eb287cd4f, 0x86061c00⟩,
  ⟨.atom 0x34455a5b851ae899465508c4b, .atom 0x15948ea9a41a97d54b8af2f3c, 0x45891000⟩,
  ⟨.atom 0x28efc9b1f161e1ff1661799f2, .atom 0x26455341579f272d50c6d2f21, 0x234b9c00⟩,
  ⟨.atom 0x2eed367f5cc5e9b20be3d68ab, .atom 0x151d9ed32a4359d6b2c5dc9cc, 0x263cc8c00⟩,
  ⟨.atom 0x32490b000db3614f4d558c0d, .atom 0x60df2f33c47ba61404a3348f, 0x144821c00⟩,
  ⟨.atom 0x389c02f4dd0adc4261461cf44, .atom 0x19eaa14ebc6fc4c6dee38e277, 0xc0081000⟩,
  ⟨.atom 0x1189608a191158a85933ba76c, .atom 0x2d27074e19a2850a2d71ad7e9, 0x1e2c98800⟩,
  ⟨.atom 0x158e25c3f161ac44ac9d51608, .atom 0x23a65f1ea76a8fee7f35fec0c, 0x64c39800⟩,
  ⟨.atom 0x2564157b61fcf8e938db7326c, .atom 0x70e42bc33a2dd1d5707cf42d, 0x23c09000⟩,
  ⟨.atom 0x15ec3a0590af1ea633f4bc4c4, .atom 0x1d0f13682fe9eeb13b1af19d7, 0x302890c00⟩,
  ⟨.atom 0x20ce276eb99f96e2a3b98babc, .atom 0x2aa912281d5c2f5a57603854f, 0x122408c00⟩,
  ⟨.atom 0x201cda70837f96206ffed855, .atom 0x1c741de6e49657b6d68aa2dc0, 0x284091c00⟩,
  ⟨.atom 0x1c87828332eed9021e4151608, .atom 0x228a9e318a119e60c61b92efe, 0x3400c1000⟩,
  ⟨.atom 0x2b59226519bf5e041a11ab26, .atom 0x314297a92a9625242eb2b8410, 0x240010400⟩,
  ⟨.atom 0x1a33f23a98971620b65fd7b70, .atom 0x288542d8a90968abfb5f9dd66, 0x2a4458c00⟩,
  ⟨.atom 0x1ccebe2bf4c1876108c86c6e1, .atom 0x2a523762ee2aa7bfef47ba48b, 0x161c89800⟩,
  ⟨.atom 0x144db0553ac2eab1b4b50304d, .atom 0x3fc8c0356609aa58867d9102a, 0x322459000⟩,
  ⟨.atom 0x33b1d9ae7f337b0453dbc52b, .atom 0x21f1f1cbd5854d815fda89925, 0x107040c00⟩,
  ⟨.atom 0x372625d3ad2977381369d27f9, .atom 0x3f1b571b967dc1f0c7830b3ba, 0xe54c9800⟩,
  ⟨.atom 0x1f9c53c396dc13324d5ff8ebd, .atom 0x300cf11826ae43e1234b052ad, 0x345811400⟩,
  ⟨.atom 0x38354ba1efd057ed7c2cc4750, .atom 0x365b9df98f9aa4ca81f2462f2, 0x2c4850c00⟩,
  ⟨.atom 0x2557a8d494d74aa9f35b259c0, .atom 0x376d7f3c3fc95726da810037e, 0xc2800400⟩,
  ⟨.atom 0xa0005e8c930981ac1cd629c7, .atom 0x359cf636ac81b0ad05ceb19d4, 0x361459800⟩,
  ⟨.atom 0x31a7d46671ea0cffd1ad59ff, .atom 0x248ea827dd5a2d255f67d7d6c, 0x3018b0400⟩,
  ⟨.atom 0x210b51474a4f9f18ae0bd1b99, .atom 0xccc575f931b7ec5106a5f5dc, 0x1a0ce8400⟩,
  ⟨.atom 0x37d6b2da6ac31e9d375a9cc00, .atom 0x22651a5508373d0c39a313ecf, 0xe6c09c00⟩,
  ⟨.atom 0xc4e179b599c4bb33ce4be3af, .atom 0xa7d9413e47b637ed4c885bf9, 0x450f1400⟩,
  ⟨.atom 0xac11aece3e33c3f4246f0022, .atom 0x2a924010bc2645ff8c8ae1d30, 0x20468c00⟩,
  ⟨.atom 0x260ab1f77f3ca8da142440668, .atom 0x2b4d76db8eb6b58bcb27ad6a8, 0x364cf9800⟩,
  ⟨.atom 0x3ccd3089b40d7e5963df44fb2, .atom 0x6172ed172804b45cc8fa2ec6, 0x2e4419800⟩,
  ⟨.atom 0x1e840bdf1ec37ba64ba346bed, .atom 0x285dd070bb30376242885a77e, 0x2880000⟩,
  ⟨.atom 0x210d77fca4d30e88c012aa0b4, .atom 0x1518147d51fc6f5e3ed9c60e6, 0x4880000⟩,
  ⟨.atom 0x257f919abaa38e630b610619c, .atom 0x3f639f6a0e8765ddc80a29465, 0x44000000⟩,
  ⟨.atom 0x4d8181e6ba2013af941892e5, .atom 0x23f0120359d1ce35db6333680, 0x47080000⟩,
  ⟨.atom 0x19181ac22c37d36e48f3c2f94, .atom 0x34be3bca90f706467ad2534c0, 0xc1880000⟩,
  ⟨.atom 0x21cd02234ef8970c928e5bf5f, .atom 0x1e7b7bf44553e90ce9b4ba1a, 0xc2000000⟩,
  ⟨.atom 0x3011e4d1860977eacf94ca1b5, .atom 0x23df323887ad9a650a3535899, 0xc6880000⟩,
  ⟨.atom 0x13906d58ceaa438d67073274, .atom 0xff43452987dc39dc38a031fa, 0xc7000000⟩,
  ⟨.atom 0x2d08798a2144f87693a69de28, .atom 0x27d6b8ff721584b665a72ab5f, 0x84000000⟩,
  ⟨.atom 0x2db5e174d2fd8914608086739, .atom 0x35f2bbf9b3baa6c61bf998ba5, 0x85800000⟩,
  ⟨.atom 0x2fbc91ac9e05c224f5a939aab, .atom 0x20d1bf165d335c88d05e33490, 0x85880000⟩,
  ⟨.atom 0x33847443c9e46b78e7872bd8f, .atom 0x236b531f878afa7c2e7403aa4, 0x86000000⟩,
  ⟨.atom 0x2ffa76a73ea73af6d46400f25, .atom 0x16ef2d1ceb21c3fee3896fd36, 0x82880000⟩,
  ⟨.atom 0x264b5bd814ff130ab7434cb69, .atom 0x121f41f244f248d92176d4582, 0x180800000⟩,
  ⟨.atom 0x3c8e3b3ef76bf1f9208b5efb7, .atom 0x39244498608e11fd60665c458, 0x181000000⟩,
  ⟨.atom 0x10dbebef9f909cbaf5d84ced3, .atom 0x1a71857002c341d238a5d8824, 0x182880000⟩,
  ⟨.atom 0xd534252b7a35db194936ff0c, .atom 0x15bae495d3476309292a94803, 0x1c2000000⟩,
  ⟨.atom 0x12aadc8f8c4cf113952041ea0, .atom 0x3388be73667751b72cf54dec8, 0x1c2880000⟩,
  ⟨.atom 0x1612d7530e449d8aa84ce8554, .atom 0x32bdc6aa3b90e2e17757e911e, 0x105800000⟩,
  ⟨.atom 0x209a9ce2fda4b64f141d60f0b, .atom 0x2a0296a6952029ea5b118d30d, 0x107800000⟩,
  ⟨.atom 0x174f02d2e7af809950087806, .atom 0x2d7641b1f85198590ad7294d0, 0x103800000⟩,
  ⟨.atom 0x3a077c252d730dda8aa9514e5, .atom 0x2ea318dd844783c1755e3187a, 0x300880000⟩,
  ⟨.atom 0x250e0b66922a838ffcfbbdc2d, .atom 0x20ac7450c6a2c4a9cdff14d49, 0x302000000⟩,
  ⟨.atom 0x3b5ef266aa03b4efcb15aa52a, .atom 0x35f3d01cbc4c556fe79288b94, 0x307000000⟩,
  ⟨.atom 0x31818dd07389d50a11d41e1cc, .atom 0x364e16c5b1f54d4eabfee19de, 0x347000000⟩,
  ⟨.atom 0xd3e8d2f808c4ef0acc388f3e, .atom 0x2bdafc863109e61c02b8aede2, 0x346000000⟩,
  ⟨.atom 0x2115b7d9474ca8130006ed1f8, .atom 0x5af2c1275bb4427a81b9f687, 0x341000000⟩,
  ⟨.atom 0x2191e17c53a3e8f4d507804fe, .atom 0x15e0f78758a154d605684c80c, 0x341800000⟩,
  ⟨.atom 0x5284f9c302fb3f2945104ba7, .atom 0x1ce1792edf0e21e7f606de889, 0x3c1800000⟩,
  ⟨.atom 0x618dad1a68b98f980abdfac, .atom 0x3fe01df77c2b7c567cd31b07e, 0x3c2880000⟩,
  ⟨.atom 0x2190af4042ee8fd09857a85c5, .atom 0x30f27f45492ce1bc2a1bc5442, 0x385080000⟩,
  ⟨.atom 0x3ea5d3fd8dcb95954e53ae556, .atom 0x2e5b58affb8098d06bc64c732, 0x383080000⟩,
  ⟨.atom 0x25d3e9c4c36448c995c6945dd, .atom 0xafe0726e0c89088fda07efdc, 0x280000000⟩,
  ⟨.atom 0x2e923a6c8b48e66f80940c5ed, .atom 0xb4284f1ecf1556e5b3b6c1c2, 0x282000000⟩,
  ⟨.atom 0x3d93e7ceb8bf0918df3262fbe, .atom 0x1996a03ef20b9a910125a85fe, 0x286880000⟩,
  ⟨.atom 0x3e78b404a459a57b3a6859985, .atom 0x2a5cd9b3a5b2a3663008358ac, 0x2c5800000⟩,
  ⟨.atom 0x35c0cc89dff133c5a264d2e91, .atom 0x2f6acb3f88f1c5a93f3ab127a, 0x2c5880000⟩,
  ⟨.atom 0x8333a8a4354da3fd5bbf6c03, .atom 0xab7070d935ccb02829ad88d5, 0x2c7080000⟩,
  ⟨.atom 0xdfc14ba65569f19c55b7949e, .atom 0x1ff061d16653bfa1b92ca6787, 0x2c6080000⟩,
  ⟨.atom 0x3501c917c97f812f045e7e8d3, .atom 0x16f58aeb30531ce34a05328da, 0x2c2000000⟩,
  ⟨.atom 0x193940789f47684dd5fd22cb5, .atom 0x850939b5789fade904d3e4c6, 0x2c1880000⟩,
  ⟨.atom 0x23230c9a7082128627981a7ab, .atom 0x1e1ef125aa17dc14d48873840, 0x243800000⟩,
  ⟨.atom 0x1cc35280fcc48101f266d2e1f, .atom 0x278321bf0404ea15f700903cb, 0x242080000⟩,
  ⟨.atom 0x1c310e9c1a3458c7e38060c5f, .atom 0x285762bc387237941c43be4b6, 0x205000000⟩,
  ⟨.atom 0x1d3cc32ac320cf593b24b8a7f, .atom 0xbc4e59e1c27bcd3213646842, 0x207880000⟩,
  ⟨.atom 0x3e4387b6c9da082afca66067f, .atom 0x3cc11ed149bda8f5bfcaf805e, 0x206800000⟩,
  ⟨.atom 0x184406d4f27b45725d57c1f6e, .atom 0x11ab338c2fee5f65ddbf98de0, 0x200000000⟩,
  ⟨.atom 0x2b2d7ee5788c9b3fab0260, .atom 0x1013022d1df49ebfe680220, 0x20000002⟩,
  ⟨.atom 0x28f1f4951398b4986d06e0, .atom 0x10ea5ebafacca9973780220, 0x366409404⟩,
  ⟨.atom 0x2317165e9480acdbe10020, .atom 0x1094a419950ff07976b0500, 0x8⟩,
  ⟨.atom 0x2a49931eb88da46ea00330, .atom 0x1069872516b26aee6a20460, 0x10⟩
]
def original129 : List Term := t0 :: t1 :: t2 :: rest

def firstSplit : Term := ⟨t1.a, .plus t1.b t2.a, t1.o⟩
def secondFlip : Term := ⟨t2.a, t2.b, Nat.xor t1.o t2.o⟩
def newProduct : Term := ⟨t2.a, .plus t1.a t2.b, t1.o⟩
def changed130 : List Term := t0 :: firstSplit :: secondFlip :: newProduct :: rest

private theorem bool_identity (a b d e c f : Bool) :
    Bool.xor (Bool.and (Bool.and a b) c) (Bool.and (Bool.and d e) f) =
      Bool.xor (Bool.and (Bool.and a (Bool.xor b d)) c)
        (Bool.xor (Bool.and (Bool.and d e) (Bool.xor c f))
          (Bool.and (Bool.and d (Bool.xor a e)) c)) := by
 cases a <;> cases b <;> cases d <;> cases e <;> cases c <;> cases f <;> decide

private theorem outputMask_identity :
    ∀ j : OutputBit, Nat.testBit (Nat.xor t1.o t2.o) j.val =
        Bool.xor (Nat.testBit t1.o j.val) (Nat.testBit t2.o j.val) := by
 decide

theorem two_terms_to_three (x : CutInput) (j : OutputBit) :
    Bool.xor (t1.eval x j) (t2.eval x j) =
      Bool.xor (firstSplit.eval x j)
        (Bool.xor (secondFlip.eval x j) (newProduct.eval x j)) := by
 have hm := outputMask_identity j
 change
    Bool.xor
      (Bool.and (Bool.and (t1.a.eval x) (t1.b.eval x)) (Nat.testBit t1.o j.val))
      (Bool.and (Bool.and (t2.a.eval x) (t2.b.eval x)) (Nat.testBit t2.o j.val)) =
    Bool.xor
      (Bool.and (Bool.and (t1.a.eval x)
        (Bool.xor (t1.b.eval x) (t2.a.eval x))) (Nat.testBit t1.o j.val))
      (Bool.xor
        (Bool.and (Bool.and (t2.a.eval x) (t2.b.eval x))
          (Nat.testBit (Nat.xor t1.o t2.o) j.val))
        (Bool.and (Bool.and (t2.a.eval x)
          (Bool.xor (t1.a.eval x) (t2.b.eval x)))
          (Nat.testBit t1.o j.val)))
 rw [hm]
 exact bool_identity (t1.a.eval x) (t1.b.eval x)
    (t2.a.eval x) (t2.b.eval x)
    (Nat.testBit t1.o j.val) (Nat.testBit t2.o j.val)

/-- Entire 129-term source and 130-term transformed decomposition agree
    on every one of 2^98 cut-state assignments and every one of 35 outputs.
    No output-vector rank inference, sampling, or unproved tensor lemma. -/
theorem original129_eq_changed130 (x : CutInput) (j : OutputBit) :
    evalTerms original129 x j = evalTerms changed130 x j := by
 change
    Bool.xor (t0.eval x j)
      (Bool.xor (t1.eval x j)
        (Bool.xor (t2.eval x j) (evalTerms rest x j))) =
    Bool.xor (t0.eval x j)
      (Bool.xor (firstSplit.eval x j)
        (Bool.xor (secondFlip.eval x j)
          (Bool.xor (newProduct.eval x j) (evalTerms rest x j))))
 have h := congrArg
    (fun p => Bool.xor (t0.eval x j) (Bool.xor p (evalTerms rest x j)))
    (two_terms_to_three x j)
 simpa only [Bool.xor_assoc] using h

theorem original_count : original129.length = 129 := by decide
theorem changed_count : changed130.length = 130 := by decide
theorem change_is_plus_one :
    changed130.length = original129.length + 1 := by decide

end GVQCC.RealV8
