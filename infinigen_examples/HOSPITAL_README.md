# 大医院场景生成系统

## 概述

这是一个基于 Infinigen 的大医院场景生成系统，可以自动生成包含以下区域的医院环境：

- **等候区 (Waiting Room)**: 大型中央等候区域，配备长椅和椅子供病人等候
- **导诊区 (Reception)**: 信息台区域，为病人答疑解惑
- **治疗区 (Treatment Zone)**: 多个诊室沿走廊排列
  - 普通诊室 (Standard Clinic): 10-20 个基本诊疗室
  - VIP 诊室 (VIP Clinic): 高端诊疗室，配备检查床

诊室入口都连接着走廊 (corridor)，排列规整成 2-3 排。

## 新增资产

系统使用以下医院专用资产：

```python
StaticBenchFactory = static_category_factory("infinigen/assets/static_assets/source/Bench")
StaticCabinetFactory = static_category_factory("infinigen/assets/static_assets/source/Cabinet")
StaticShelfFactory = static_category_factory("infinigen/assets/static_assets/source/Shelf", tag_support=True, z_dim=2)
StaticChairFactory = static_category_factory("infinigen/assets/static_assets/source/Chair")
StaticDentalunitFactory = static_category_factory("infinigen/assets/static_assets/source/Dentalunit")
StaticFronttableFactory = static_category_factory("infinigen/assets/static_assets/source/Fronttable")
StaticInternchairFactory = static_category_factory("infinigen/assets/static_assets/source/Internchair")
StaticRectangleFactory = static_category_factory("infinigen/assets/static_assets/source/Rectangle")
StaticSofaFactory = static_category_factory("infinigen/assets/static_assets/source/Sofa")
StaticTableFactory = static_category_factory("infinigen/assets/static_assets/source/Table")
```

## 使用方法

### 基本命令

```bash
blender -b -P infinigen_examples/generate_hospital.py -- \
    --output_folder /path/to/output \
    --seed 0 \
    --task coarse mesh_save \
    --configs hospital
```

### 自定义诊室数量

```bash
blender -b -P infinigen_examples/generate_hospital.py -- \
    --output_folder /path/to/output \
    --seed 0 \
    --task coarse mesh_save \
    --configs hospital \
    --overrides \
        hospital_room_constraints.num_clinics=15 \
        hospital_room_constraints.num_vip_clinics=3
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `num_clinics` | 15 | 诊室总数（普通 + VIP） |
| `num_vip_clinics` | 3 | VIP 诊室数量 |
| `has_large_waiting_room` | True | 是否创建大型等候区 |
| `seed` | 0 | 随机种子 |

## 系统架构

### 1. 语义标签 (tags.py)

新增的房间类型语义标签：
- `HospitalWaitingRoom`: 等候区
- `HospitalReception`: 导诊区
- `HospitalClinic`: 普通诊室
- `HospitalVIPClinic`: VIP 诊室
- `HospitalCorridor`: 走廊
- `HospitalTreatmentRoom`: 治疗室
- `HospitalExaminationRoom`: 检查室

新增的家具语义标签：
- `WaitingBench`: 等候长椅
- `WaitingChair`: 等候椅
- `ReceptionDesk`: 导诊台
- `DoctorDesk`: 医生办公桌
- `DoctorChair`: 医生椅
- `PatientChair`: 病人椅
- `ExaminationTable`: 检查床
- `MedicalCabinet`: 医疗柜
- `MedicalShelf`: 医疗架

### 2. 约束系统

#### 房间约束 (hospital_room_constraints.py)
定义医院房间的布局规则：
- 等候区连接到入口
- 导诊区靠近等候区
- 走廊连接到等候区
- 诊室沿走廊排列（2-3 排）
- 房间大小和比例约束

#### 家具约束 (hospital_furniture_constraints.py)
定义医院家具的放置规则：
- 等候区：长椅靠墙，椅子排列整齐
- 导诊区：导诊台靠近入口
- 诊室：医生桌、病人椅、医疗柜合理布置
- VIP 诊室：额外配备检查床
- 走廊：保持畅通，最小化障碍物

### 3. 语义映射 (hospital_semantics.py)

将资产工厂映射到医院语义角色，定义了：
- 等候区家具（长椅、椅子、茶几）
- 导诊台
- 诊室家具（医生桌、医生椅、病人椅）
- 医疗设备（检查床、医疗柜、医疗架）
- 装饰物品（植物、展示品）

## 文件结构

```
infinigen/
├── infinigen/
│   ├── core/
│   │   └── tags.py                              # 新增医院语义标签
│   └── assets/
│       └── static_assets/
│           ├── __init__.py                      # 导出医院资产工厂
│           └── static_category.py               # 定义医院资产工厂
└── infinigen_examples/
    ├── constraints/
    │   ├── hospital_semantics.py                # 医院语义映射
    │   ├── hospital_room_constraints.py         # 医院房间约束
    │   ├── hospital_furniture_constraints.py    # 医院家具约束
    │   └── util.py                              # 更新房间类型
    ├── configs_indoor/
    │   └── hospital.gin                         # 医院配置
    ├── generate_hospital.py                     # 主入口脚本
    └── util/
        └── generate_indoors_util.py             # 工具函数
```

## 示例场景配置

### 小型诊所（5 个诊室）

```bash
blender -b -P infinigen_examples/generate_hospital.py -- \
    --output_folder /path/to/output \
    --seed 42 \
    --task coarse mesh_save \
    --configs hospital \
    --overrides \
        hospital_room_constraints.num_clinics=5 \
        hospital_room_constraints.num_vip_clinics=1
```

### 大型医院（20 个诊室，5 个 VIP）

```bash
blender -b -P infinigen_examples/generate_hospital.py -- \
    --output_folder /path/to/output \
    --seed 100 \
    --task coarse mesh_save \
    --configs hospital \
    --overrides \
        hospital_room_constraints.num_clinics=20 \
        hospital_room_constraints.num_vip_clinics=5 \
        compose_indoors.solve_steps_large=500
```

## 注意事项

1. **资产文件**: 确保以下资产目录存在并包含有效的 3D 模型文件：
   - `infinigen/assets/static_assets/source/Bench`
   - `infinigen/assets/static_assets/source/Cabinet`
   - `infinigen/assets/static_assets/source/Chair`
   - `infinigen/assets/static_assets/source/Dentalunit`
   - `infinigen/assets/static_assets/source/Fronttable`
   - `infinigen/assets/static_assets/source/Internchair`
   - `infinigen/assets/static_assets/source/Shelf`
   - `infinigen/assets/static_assets/source/Sofa`
   - `infinigen/assets/static_assets/source/Table`

2. **求解时间**: 大型医院场景可能需要较长的求解时间，可以通过增加 `solve_steps` 参数来提高质量。

3. **内存使用**: 生成大型场景时，确保有足够的 RAM（建议 16GB+）。

4. **Blender 版本**: 需要使用 Blender 3.x 或更高版本。

## 故障排除

### 房间生成失败
- 增加求解步数：`compose_indoors.solve_steps_large=500`
- 减少诊室数量
- 更改随机种子

### 资产加载失败
- 检查资产路径是否正确
- 确保资产文件格式 supported（.blend 等）
- 检查资产文件是否存在

## 扩展

如需添加更多医院功能（如手术室、病房、药房等），可以：
1. 在 `tags.py` 中添加新的语义标签
2. 在约束文件中定义新的约束规则
3. 在语义映射中关联新的资产
