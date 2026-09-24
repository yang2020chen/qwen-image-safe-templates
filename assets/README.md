# Qwen-Image-2.1 Benchmark Results & Input References

本目录收录了在 **AMD Radeon RX 7900 XTX 24GB (ROCm 7.2)** 上运行 **Qwen-Image-2.1** 10 大战役实测生成的全量高清结果图，以及复现实验所需的输入参考物料。

---

## 1. 10 大战役测试生成结果图清单（根目录）

严格对应评测总表中的 10 大场景实机生成成果：

| 战役编号 | 场景分类 | 生成图文件名 | 分辨率模式 | 显存与耗时 (RX 7900 XTX) | 画面核心验收特征 |
|---|---|---|---|---|---|
| **01** | 微距写实肖像 | [`01_test_macro_realism_2k.png`](./01_test_macro_realism_2k.png) | 1376 × 1824 | 19.5 GB · 92.4s | SSS凝脂肤质、微距毛孔与自然细发丝 |
| **02** | 中英文宋体排版 | [`02_test_typography_bilingual_2k.png`](./02_test_typography_bilingual_2k.png) | 1376 × 1824 | 19.4 GB · 91.8s | “VOGUE ORIENT” 与 “东方留白 美学新生” 零错字宋体排版 |
| **03** | 严苛个位数计数 | [`03_test_strict_counting_2k.png`](./03_test_strict_counting_2k.png) | 1824 × 1216 | 19.2 GB · 88.5s | 1壶、3盏、1香炉、2枝荷花绝对准确 |
| **04A (对比组)** | 坏基线: Issue 16435 翻车 | [`04a_test_suit_edit_fail_issue16435.png`](./04a_test_suit_edit_fail_issue16435.png) | 1376 × 1824 | 102.4s | 未对齐网格：满屏黑斑与碎石化背景彻底崩溃 |
| **04A** | 纯文本局部换装 (修复后) | [`04a_test_suit_edit_safe_res1056.png`](./04a_test_suit_edit_safe_res1056.png) | 928 × 1216 | 17.8 GB · **49.2s** | 安全网格：背景与冷白皮 100% 锁死，高级深灰西装 |
| **04B** | 双图高定物料迁移 | [`04b_test_couture_dress_transfer.png`](./04b_test_couture_dress_transfer.png) | 928 × 1216 | 18.2 GB · 55.1s | 欧根纱半透明光泽、高定洋装面料纹理精准复刻 |
| **05** | 三视图动态姿势重绘 | [`05_test_dynamic_pose_recreation.png`](./05_test_dynamic_pose_recreation.png) | 1824 × 1216 | 18.9 GB · 62.3s | 汉服三视图驱动暮色水榭漫步回眸，身份一致 |
| **06** | 商业香水人货焦散 | [`06_test_commercial_perfume_ad.png`](./06_test_commercial_perfume_ad.png) | 928 × 1216 | 18.1 GB · 51.4s | 水晶瓶切面琥珀色液体焦散折射至右手皮肤 |
| **07** | 满月荷塘夜景重绘 | [`07_test_moonlit_lotus_relighting.png`](./07_test_moonlit_lotus_relighting.png) | 928 × 1216 | 18.4 GB · 39.2s | 暮色满月夜景，冷白皮月光与宫灯双轮廓光 |
| **08** | 吹制水晶鹤 RGBA | [`08_test_rgba_transparent_crane.png`](./08_test_rgba_transparent_crane.png) | 1536 × 1536 | 20.1 GB · 98.2s | 原生 4 通道 Alpha 资产，免抠绿幕纯透明底 |
| **09** | 10位肖像并发群像 | [`09_test_group_10ref_santorini.png`](./09_test_group_10ref_santorini.png) | 1216 × 928 | 21.1 GB · 69.8s | 吞吐 ~2万 Tokens，圣托里尼 10 人合影无畸变 |
| **10** | 金色云海超现实仙女 | [`10_test_surreal_fairy_wings.png`](./10_test_surreal_fairy_wings.png) | 1536 × 1536 | 20.3 GB · 97.6s | 背生巨大透明琉璃蝶翼，解剖级骨骼结构 |

---

## 2. 实验复现输入参考物料（`input_references/` 目录）

- `m1_base_beauty_2k.png`：微距美女底图原图 (1376 × 1824)
- `m1_base_beauty_hollow_red_2k.png`：空心红圈选区标注底图 (1376 × 1824)
- `m2_couture_dress_ref.png`：高级成衣面料与剪裁参考图 (1376 × 1824)
- `m3_perfume_bottle_ref.png`：切面奢华水晶香水瓶参考图 (1536 × 1536)
- `m4_character_sheet_ref.png`：汉服角色正面/侧面/背面三视图设定集 (1536 × 1536)
- `m5_avatar_01.png` ~ `m5_avatar_10.png`：10 位不同族裔女性肖像参考图库 (1024 × 1024)
