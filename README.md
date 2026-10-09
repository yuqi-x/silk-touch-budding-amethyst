# Silk Touch Budding Amethyst（精准采集可采集母岩）

修复 26.2 里**紫水晶母岩挖了什么都不掉**的问题：用带**精准采集**的工具挖母岩，掉落母岩本身。

## 怎么实现的

只做一件事：**覆盖原版的那一条掉落表**。

```
data/minecraft/loot_table/blocks/budding_amethyst.json
```

路径要和原版一模一样才会顶掉它。原版 26.2 里这条掉落表只有 `{"type": "minecraft:block", "random_sequence": ...}`，没写 `pools` —— 按规则就是"破坏后无掉落"，精准采集也一样。本数据包把它补成"有精准采集才掉母岩"：

- `minecraft:match_tool` + `predicate.predicates.minecraft:enchantments` 要求 `minecraft:silk_touch` ≥ 1 级（26.2 的新写法，旧版的 `enchantments` 平铺写法已失效）
- 额外挂一条 `minecraft:survives_explosion`，避免用 TNT 之类"炸出"母岩
- 掉落物就是 `minecraft:budding_amethyst`，与自然生成的母岩完全一致：能正常随机刻、长紫晶芽

## 服务端兼容性（重点）

掉落表属于**服务端数据**，所以：

| 形态 | 放哪 | 适用 |
|------|------|------|
| `silk_touch_budding_amethyst-1.0.0.jar` | 服务端 `mods/` | Fabric 服务端（原版服务端不支持 mod） |
| `silk_touch_budding_amethyst-datapack.zip` 或文件夹 | 服务端 `world/datapacks/` | **任何服务端**：原版、Fabric、Paper……客户端不用装 |

装到服务端 ⇒ 所有玩家都有这个行为；纯客户端装只在单人/自己开的世界有效。

## 打包

```powershell
python build.py
python build.py --out "D:\so\me\where"
```

产物（`dist/`）：模组 jar、数据包文件夹、数据包 zip，三种内容一致。打包前会做 JSON 解析门禁 + 掉落表结构断言，坏 JSON 进不了产物（进游戏会直接变"安全错误"，很烦）。

## 安装 & 验证

1. 数据包丢进 `<世界目录>/datapacks/`（服务端就是 `world/datapacks/`）
2. 游戏内 `/reload`，再用 `/datapack list` 确认它已启用（loot table 支持热重载，不用重启）
3. 拿精准采集镐挖一块母岩 → 应该掉出母岩；换成无精准采集的镐 → 依旧什么都不掉

## 与其他模组共存

本包只碰这一条掉落表，不新增物品、不改方块，和材质包、生电模组没有冲突。可以和 `craftable_budding_amethyst`（母岩可合成）同时装，二者互不干扰。
