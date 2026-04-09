# 大规模口腔医院场景生成 README

## 概述

本模块基于 Infinigen 的室内场景管线，新增了一套用于生成**大规模口腔医院 / 口腔门诊**的程序化系统。

当前版本重点支持：

- **5–30 个诊室**的可伸缩布局
- **约 25% VIP 诊室**
- **每个诊室强制包含 1 个牙床 + 1 个水槽**
- **普通 / VIP 诊室面积参数化**
- VIP 诊室自带**小休息区**（桌子 + 沙发）
- **更规整的整体平面**：默认采用 **矩形**，也支持 **T 字形**
- 候诊区与导诊 / 前台区可做成**开放式公共前场**
- 支持空间向中部收拢，更接近真实口腔门诊的共享核心

---

## 当前默认布局

### 默认：`rectangular`

默认平面不再是“这里突出一个房间、那里再凸出去一块”的拼接感布局，而是更接近真实门诊流线的：

- 左 / 前侧：一个**开放式公共前场**
- 公共前场内部：**大候诊区 + 小导诊 / 前台区**
- 候诊区与导诊区之间默认通过开口连通，不做强硬封闭分隔
- 公共前场与临床区之间：默认通过**1 个主入口**接入主走廊，也可切换为 2 个入口
- 临床区内部：一条**主干道式走廊**
- 诊疗区：诊室沿主走廊两侧展开
- 当诊室数量较大时（默认 `>= 22`），矩形模式会自动切成**双走廊 / 三排诊区**
- 当诊室数量进一步增多时（默认 `>= 28`），会继续切成**三走廊 / 四排诊区**
- 支持空间：`Examination` / `Treatment` 默认成对相邻，形成**支持功能簇**
- 普通诊室：连续组成一个**普通诊室簇**
- VIP：默认在远端形成一个**VIP 诊室簇**

这种结构更接近真实的大型口腔门诊：

- 前公区和临床区关系更清楚
- 候诊 / 导诊区更像真实的开放式前厅
- 主走廊更像治疗区主干道
- 普通诊室、VIP 诊室、支持房间的分区关系更清晰
- 支持区不是挂在远端的“附件房间”
- 外轮廓更规整，整体更接近 **规则矩形门诊楼层**

对于大场景的矩形模式，默认会按规模继续升级：

- 左 / 前侧仍然是开放式候诊 + 导诊前场
- `22+` 诊室：临床区改成**上下两条平行走廊**，诊区压缩成**三排**
- `28+` 诊室：进一步升级为**三条平行走廊**，诊区压缩成**四排**
- `Examination + Treatment` 会作为中部支持簇放在两条走廊之间
- 默认 `vip_cluster_side='split'` 时，VIP 也会优先收拢到中部带状簇里

### 可选：`t_shape`

如果你后面仍然想尝试带分叉的平面，也可以切到：

```gin
plan_form = 't_shape'
```

T 字形模式下：

- 前场后方会进入统一分叉点
- 支持房间更靠近分叉节点
- 上下两翼会更明显

适合你想保留一点“门诊双翼感”的场景。

---

## 当前能力

### 1. 诊室规模

支持总诊室数：

- 最小：`5`
- 最大：`30`
- 默认：`12`

### 2. VIP 比例

通过 `vip_ratio` 控制 VIP 诊室占比，默认：

```gin
vip_ratio = 0.25
```

例如：

- 12 个诊室 -> 3 个 VIP
- 16 个诊室 -> 4 个 VIP
- 20 个诊室 -> 5 个 VIP
- 30 个诊室 -> 8 个 VIP（四舍五入）

### 3. 诊室面积可配置

默认采用“面积驱动”的方式控制诊室尺寸：

- 普通诊室：`23.0 ㎡`
- VIP 诊室：`34.8 ㎡`

并通过长宽比推导近似尺寸。当前默认进一步偏向“更紧凑、少长条感”的比例：

- 普通诊室约：`4.3m x 5.4m`
- VIP 诊室约：`5.4m x 6.4m`

只要修改：

- `standard_clinic_area`
- `vip_clinic_area`

就能保证**同类诊室面积基本一致**。

### 4. 普通诊室配置

每个普通诊室至少包含：

- 1 个牙床（`StaticDentalunitFactory`）
- 1 个水槽（`StandingSinkFactory`）
- 医生 / 助手椅
- 柜体
- 少量桌椅类辅助家具

### 5. VIP 诊室配置

每个 VIP 诊室至少包含：

- 1 个牙床
- 1 个水槽
- 医生 / 助手椅
- 柜体
- 1 个沙发
- 1~2 张桌子

VIP 诊室更大，并通过家具布置形成“诊疗区 + 小休息区”的效果。

### 6. 公共与支持空间

当前版本包含：

- 候诊区（Waiting Room）
- 导诊 / 前台区（Reception）
- 主走廊（Corridor）
- 影像 / 咨询支持室（沿用 `HospitalExaminationRoom`）
- 消毒 / 治疗准备区（沿用 `HospitalTreatmentRoom`）

在口腔医院预设中：

- `HospitalExaminationRoom` 可理解为 **影像 / 咨询 / 初诊支持空间**
- `HospitalTreatmentRoom` 可理解为 **消毒 / 器械准备 / 治疗准备空间**

当前优化的重点，是让这两个支持房间更像**共享核心**，并且在矩形方案里尽量往诊区中部靠，而不是挂在翼端的“附属房间”。

另外，矩形默认布局里：

- Waiting 与 Reception 在语义上仍然分开，便于分别布置家具
- 但两者之间通过 `opens` 开口处理成**开放式前场**
- 默认是**大候诊区 + 小导诊区**
- 默认通过 **1 个主入口** 接入临床主走廊
- 如有需要也可以改回 **2 个入口**

---

## 新增 / 主要文件

### 主入口
- `infinigen_examples/generate_dental_hospital.py`

### floor plan
- `infinigen_examples/constraints/dental_hospital_floorplan.py`

### 家具与设备约束
- `infinigen_examples/constraints/dental_hospital_furniture_constraints.py`

### 房间常量配置
- `infinigen_examples/constraints/dental_hospital_room_constraints.py`

### 语义映射
- `infinigen_examples/constraints/dental_hospital_semantics.py`

### gin 配置
- `infinigen_examples/configs_indoor/dental_hospital.gin`

---

## 运行方式

### 默认运行（矩形）

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 0 \
    --task coarse mesh_save \
    --configs dental_hospital
```

### 快速测试：5 个诊室

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 0 \
    --task coarse \
    --configs dental_hospital \
    --overrides \
        dental_hospital_floorplan.num_clinics=5 \
        compose_dental_hospital.solve_steps_large=40 \
        compose_dental_hospital.solve_steps_medium=20 \
        compose_dental_hospital.solve_steps_small=10 \
        compose_dental_hospital.num_floating=0
```

### 指定 16 个诊室

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 1 \
    --task coarse mesh_save \
    --configs dental_hospital \
    --overrides \
        dental_hospital_floorplan.num_clinics=16
```

### 指定 30 个诊室

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 2 \
    --task coarse mesh_save \
    --configs dental_hospital \
    --overrides \
        dental_hospital_floorplan.num_clinics=30
```

### 切换为 T 字形布局

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 3 \
    --task coarse mesh_save \
    --configs dental_hospital \
    --overrides \
        dental_hospital_floorplan.plan_form='t_shape'
```

### 调整普通 / VIP 诊室面积

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 4 \
    --task coarse mesh_save \
    --configs dental_hospital \
    --overrides \
        dental_hospital_floorplan.standard_clinic_area=24.0 \
        dental_hospital_floorplan.vip_clinic_area=36.0
```

### 调整公共前场与主走廊连接方式

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 6 \
    --task coarse mesh_save \
    --configs dental_hospital \
    --overrides \
        dental_hospital_floorplan.public_corridor_entry_count=2
```

### 调整导诊区尺寸

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 7 \
    --task coarse mesh_save \
    --configs dental_hospital \
    --overrides \
        dental_hospital_floorplan.reception_width_ratio=0.22
```

### 调整 VIP 诊区位置

```bash
blender -b -P infinigen_examples/generate_dental_hospital.py -- \
    --output_folder /path/to/output \
    --seed 5 \
    --task coarse mesh_save \
    --configs dental_hospital \
    --overrides \
        dental_hospital_floorplan.vip_cluster_side='bottom' \
        dental_hospital_floorplan.vip_at_far_end=False
```

---

## 关键参数

### 核心布局参数

| 参数 | 说明 |
|---|---|
| `num_clinics` | 总诊室数量，支持 5–30 |
| `vip_ratio` | VIP 诊室比例 |
| `plan_form` | 整体形态，支持 `t_shape` / `rectangular` |
| `corridor_width` | 走廊基础宽度 |
| `front_buffer_length` | 前场与临床区之间的过渡长度 |
| `public_zone_depth` | 候诊区与前台区统一深度；设置后外轮廓更整齐 |
| `lobby_width` | 前场候诊 / 前台总宽度 |
| `reception_width_ratio` | 前台在前场中的宽度占比 |
| `wing_standard_ratio` | 标准诊室向后翼 / 核心后段偏移的比例，值越大越偏向翼区 |
| `corridor_connector_length` | 主走廊与分叉节点的重叠长度，影响 T 字节点稳定性 |
| `multi_corridor_threshold` | 矩形模式切换到“双走廊 / 三排诊区”的诊室数量阈值 |
| `four_row_threshold` | 矩形模式进一步切换到“三走廊 / 四排诊区”的诊室数量阈值 |
| `vip_cluster_side` | VIP 集中在 `top` 或 `bottom` 侧 |
| `vip_at_far_end` | `True` 表示 VIP 在该翼远端；`False` 表示更靠近核心 |

### 诊室尺寸参数

| 参数 | 说明 |
|---|---|
| `standard_clinic_area` | 普通诊室目标面积（㎡） |
| `standard_clinic_aspect_ratio` | 普通诊室宽深比 |
| `vip_clinic_area` | VIP 诊室目标面积（㎡） |
| `vip_clinic_aspect_ratio` | VIP 诊室宽深比 |
| `standard_clinic_width` / `standard_clinic_depth` | 当面积参数设为 `None` 时的回退宽深 |
| `vip_clinic_width` / `vip_clinic_depth` | 当面积参数设为 `None` 时的回退宽深 |

### 支持空间参数

| 参数 | 说明 |
|---|---|
| `support_room_width` | 支持房间宽度 |
| `examination_depth` | 影像 / 咨询支持房间深度 |
| `treatment_depth` | 消毒 / 治疗准备房间深度 |

### 求解参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `compose_dental_hospital.solve_steps_large` | 320 | 大件家具求解步数 |
| `compose_dental_hospital.solve_steps_medium` | 180 | 中件求解步数 |
| `compose_dental_hospital.solve_steps_small` | 60 | 小件求解步数 |

如果只是验证布局，建议先降低求解步数做 smoke test。

---

## 当前用到的主要资产

### 静态资产

- `StaticDentalunitFactory`：牙床 / 牙椅
- `StaticFronttableFactory`：前台桌
- `StaticInternchairFactory`：医生 / 助手椅
- `StaticCabinetFactory`：柜体
- `StaticBenchFactory`：候诊长椅
- `StaticChairFactory`：椅子
- `StaticSofaFactory`：沙发
- `StaticTableFactory`：桌子

### 程序资产

- `StandingSinkFactory`：水槽

用于满足“每个诊室必须有一个水槽”的要求。

---

## 设计思路

### 为什么不直接硬改 `generate_indoors.py`

`generate_indoors.py` 是通用室内主流程，直接把口腔医院逻辑塞进去会让住宅与医疗场景耦合过深，不利于维护。

因此当前实现采用：

- 单独入口：`generate_dental_hospital.py`
- 单独 floor plan：`dental_hospital_floorplan.py`
- 单独约束与 gin 配置
- 尽量复用 Infinigen 现有室内求解 / 门窗 / 墙地顶 / 相机流程

### 为什么强调规整平面

真实的大型口腔门诊通常具有以下特点：

- 前台、导诊、候诊区关系明确
- 临床区与公共区之间有过渡
- 支持空间位于中部或主流线附近
- 普通诊室成排、尺寸统一
- VIP 诊区通常会连续聚集，而不是零散穿插
- 整体轮廓更接近 **矩形 / T 字形 / 规整双翼形**，而不是很多小凸起

这也是当前 floor plan 的主要优化方向。

---

## 当前局限

当前版本优先解决的是：

- 大规模诊室布局
- 普通 / VIP 诊室面积统一
- 每个诊室的牙床 / 水槽强制配置
- 更规整的总平面
- 更合理的前区 / 支持区 / VIP 子分区关系

尚未细化的部分包括：

- 更真实的影像设备（CBCT / 全景机）
- 更细的洁污流线
- 专门的护士站 / 医生站 / 库房 / 清洁间
- 多核心筒 / 多楼层的大型医院逻辑
- 更精细的牙科专用设备代理

---

## 推荐实践

如果你的目标是快速做批量生成或数据集渲染，建议优先：

- 测试规模：`5 / 12 / 20 / 30`
- 默认 `vip_ratio = 0.25`
- 用 `standard_clinic_area` / `vip_clinic_area` 控制诊室大小
- 先用 `rectangular` 做主方案
- 如果你想尝试带分叉的组织，再切 `t_shape`
- 先用低求解步数验证，再拉高做正式生成

---

## 总结

这一版口腔医院系统已经支持：

- **5–30 个诊室**的可伸缩布局
- **约 25% VIP 诊室**
- **每个诊室必须有牙床和水槽**
- **普通 / VIP 诊室面积可独立参数化**
- VIP 诊室带**沙发 + 桌子**的小休息区
- 候诊区与导诊区相邻
- 支持区更靠近中部
- 默认采用更规整的 **矩形**，并可切换为 **T 字形**

如果后续还要继续增强真实感，建议下一步优先补：

1. 更真实的影像 / 消毒支持空间资产
2. 更细的后勤 / staff-only 房间语义
3. 更严格的医院流线约束
4. 更复杂的大型门诊多翼布局
