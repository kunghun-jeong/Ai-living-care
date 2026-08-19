// ============================================================
// LivingCare 지식그래프 v2 - 확정 스키마 (Device/Function/State 분리)
// generate_cypher_v2.py 실행 결과. 원본 JSON을 고친 뒤 재생성할 것.
// ============================================================

// --- 제약조건 ---
CREATE CONSTRAINT axis_id_unique IF NOT EXISTS FOR (a:Axis) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE;
CREATE CONSTRAINT function_id_unique IF NOT EXISTS FOR (f:Function) REQUIRE f.function_id IS UNIQUE;
CREATE CONSTRAINT axis_rule_id_unique IF NOT EXISTS FOR (r:AxisKnowledge) REQUIRE r.rule_id IS UNIQUE;
CREATE CONSTRAINT device_knowledge_id_unique IF NOT EXISTS FOR (k:DeviceKnowledge) REQUIRE k.knowledge_id IS UNIQUE;
CREATE CONSTRAINT state_id_unique IF NOT EXISTS FOR (s:State) REQUIRE s.state_id IS UNIQUE;

// --- Axis ---
CREATE (:Axis {id: "onto:saref/WellBeing", label: "WellBeing"});
CREATE (:Axis {id: "onto:saref/Safety", label: "Safety"});
CREATE (:Axis {id: "onto:saref/Comfort", label: "Comfort"});

// --- Device ---
CREATE (:Device {device_id: "cap:actuator", device_class: "Actuator", slot: "actuator", risk_tier: "adjustable", cost_hint: "low", source: "saref_auto_extracted", saref_uri: "https://saref.etsi.org/core/Actuator"});
CREATE (:Device {device_id: "cap:doorswitch", device_class: "DoorSwitch", slot: "doorswitch", risk_tier: "safety_critical", cost_hint: "low", source: "saref_auto_extracted", saref_uri: "https://saref.etsi.org/core/DoorSwitch"});
CREATE (:Device {device_id: "cap:lightswitch", device_class: "LightSwitch", slot: "light", risk_tier: "adjustable", cost_hint: "low", source: "saref_auto_extracted", saref_uri: "https://saref.etsi.org/core/LightSwitch"});
CREATE (:Device {device_id: "cap:meter", device_class: "Meter", slot: "meter", risk_tier: "adjustable", cost_hint: "low", source: "saref_auto_extracted", saref_uri: "https://saref.etsi.org/core/Meter"});
CREATE (:Device {device_id: "cap:sensor", device_class: "Sensor", slot: "sensor", risk_tier: "adjustable", cost_hint: "low", source: "saref_auto_extracted", saref_uri: "https://saref.etsi.org/core/Sensor"});
CREATE (:Device {device_id: "cap:smokesensor", device_class: "SmokeSensor", slot: "smoke", risk_tier: "safety_critical", cost_hint: "low", source: "saref_auto_extracted", saref_uri: "https://saref.etsi.org/core/SmokeSensor"});
CREATE (:Device {device_id: "cap:temperaturesensor", device_class: "TemperatureSensor", slot: "temperature", risk_tier: "adjustable", cost_hint: "low", source: "saref_auto_extracted", saref_uri: "https://saref.etsi.org/core/TemperatureSensor"});
CREATE (:Device {device_id: "cap:motionsensor", device_class: "MotionSensor", slot: "motion", risk_tier: "adjustable", cost_hint: "low", source: "custom_extension"});
CREATE (:Device {device_id: "cap:wearable_vitals", device_class: "WearableVitalsMonitor", slot: "heartrate", risk_tier: "adjustable", cost_hint: "low", source: "custom_extension"});
CREATE (:Device {device_id: "cap:limo_robot_agent", device_class: "LimoRobot", slot: "person_presence", risk_tier: "safety_critical", cost_hint: "high", source: "custom_extension"});

// --- Function (reachability만, 세부 명령 목록은 worker가 별도 관리) ---
CREATE (:Function {function_id: "func:actuator:ActuatingFunction", name: "ActuatingFunction", reachable: true});
MATCH (d:Device {device_id: "cap:actuator"}), (f:Function {function_id: "func:actuator:ActuatingFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:doorswitch:OpenCloseFunction", name: "OpenCloseFunction", reachable: true});
MATCH (d:Device {device_id: "cap:doorswitch"}), (f:Function {function_id: "func:doorswitch:OpenCloseFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:lightswitch:OnOffFunction", name: "OnOffFunction", reachable: true});
MATCH (d:Device {device_id: "cap:lightswitch"}), (f:Function {function_id: "func:lightswitch:OnOffFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:meter:MeteringFunction", name: "MeteringFunction", reachable: true});
MATCH (d:Device {device_id: "cap:meter"}), (f:Function {function_id: "func:meter:MeteringFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:sensor:SensingFunction", name: "SensingFunction", reachable: true});
MATCH (d:Device {device_id: "cap:sensor"}), (f:Function {function_id: "func:sensor:SensingFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:smokesensor:EventFunction", name: "EventFunction", reachable: true});
MATCH (d:Device {device_id: "cap:smokesensor"}), (f:Function {function_id: "func:smokesensor:EventFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:smokesensor:SensingFunction", name: "SensingFunction", reachable: true});
MATCH (d:Device {device_id: "cap:smokesensor"}), (f:Function {function_id: "func:smokesensor:SensingFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:temperaturesensor:SensingFunction", name: "SensingFunction", reachable: true});
MATCH (d:Device {device_id: "cap:temperaturesensor"}), (f:Function {function_id: "func:temperaturesensor:SensingFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:motionsensor:SensingFunction", name: "SensingFunction", reachable: true});
MATCH (d:Device {device_id: "cap:motionsensor"}), (f:Function {function_id: "func:motionsensor:SensingFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:wearable_vitals:SensingFunction", name: "SensingFunction", reachable: true});
MATCH (d:Device {device_id: "cap:wearable_vitals"}), (f:Function {function_id: "func:wearable_vitals:SensingFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:limo_robot_agent:NavigateFunction", name: "NavigateFunction", reachable: true});
MATCH (d:Device {device_id: "cap:limo_robot_agent"}), (f:Function {function_id: "func:limo_robot_agent:NavigateFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);
CREATE (:Function {function_id: "func:limo_robot_agent:ObserveFunction", name: "ObserveFunction", reachable: true});
MATCH (d:Device {device_id: "cap:limo_robot_agent"}), (f:Function {function_id: "func:limo_robot_agent:ObserveFunction"}) CREATE (d)-[:HAS_FUNCTION]->(f);

// --- DeviceKnowledge ---
// 지금은 실제 근거(rationale/source) 있는 항목이 없어 아무것도 생성하지 않음.
// 예: LIMO 로봇의 SLAM 사양서를 확인한 뒤, 아래 형태로 직접 추가할 것:
//
// CREATE (k:DeviceKnowledge {knowledge_id: "dk:limo:map_coverage",
//   statement: "이 로봇은 사전 매핑된 실내 전체 맵을 보유하고 있다",
//   rationale: "...", source: "LIMO SLAM 사양서 v_.._, 확인일 ____"})
// WITH k MATCH (d:Device {device_id: "cap:limo_robot_agent"}) CREATE (d)-[:HAS_DEVICE_KNOWLEDGE]->(k);

// --- State (배터리, 초기 시드값 - AI agent가 실제 관측값으로 덮어써야 함) ---
CREATE (:State {state_id: "state:limo_robot_agent:battery_level", key: "battery_level", updated_at: "2026-08-17T05:40:08.402588+00:00", updated_by: "seed_script"});
MATCH (d:Device {device_id: "cap:limo_robot_agent"}), (s:State {state_id: "state:limo_robot_agent:battery_level"}) CREATE (d)-[:HAS_STATE]->(s);

// --- AxisKnowledge ---
CREATE (:AxisKnowledge {slot: "motion", time_context: "day", threshold_hours: 4, severity: "concern", rationale: "주간에 4시간 이상 활동 신호가 없으면 우려 상황으로 본다. 상용 텔레케어 시스템의 12~24시간 기준보다 보수적으로 잡은 이유는, 낙상 등 응급상황 발견이 늦어질수록 예후가 나빠지기 때문 (낙상은 65세 이상 입원의 주요 원인 중 하나).", source: "Red Alert Telecare 상용 기준(12~24h)을 참고해 보수적으로 재설정", rule_id: "wb_r1_no_motion_day"});
MATCH (a:Axis {id: "onto:saref/WellBeing"}), (r:AxisKnowledge {rule_id: "wb_r1_no_motion_day"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "motion", time_context: "night", threshold_hours: 8, severity: "info_only", rationale: "야간에는 수면 중이라 무동작이 정상이다. 8시간까지는 우려 상황으로 취급하지 않는다 — 밤 시간대에 지나치게 민감하면 불필요한 로봇 출동/알림으로 오히려 수면을 방해함.", source: "특허 US10226177 - 낮/밤 별도 임계값 설계 관행", rule_id: "wb_r2_no_motion_night"});
MATCH (a:Axis {id: "onto:saref/WellBeing"}), (r:AxisKnowledge {rule_id: "wb_r2_no_motion_night"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "motion", location: "kitchen", time_context: "night", condition: "visit_detected", severity: "info_only", rationale: "야간 주방 방문은 그 자체로 위험 신호는 아니지만, 수면장애나 야간 저혈당 등의 간접 지표로 기록해둘 가치가 있다. 당장 조치하지 않고 패턴으로만 축적.", source: "StackCare 특허(US12340890) - 야간 주방 방문 모니터링 관행", rule_id: "wb_r3_night_kitchen_visit"});
MATCH (a:Axis {id: "onto:saref/WellBeing"}), (r:AxisKnowledge {rule_id: "wb_r3_night_kitchen_visit"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "heartrate", threshold_hours: 6, severity: "mild_concern", rationale: "웨어러블 동기화 자체는 착용 여부/배터리 문제일 수 있어 단독으로는 약한 신호로만 취급. 다른 규칙과 동시 위반시에만 confidence를 낮춘다 (오탐 방지).", source: "설계팀 자체 정책 (웨어러블은 단독 신뢰도가 낮은 센서로 취급)", rule_id: "wb_r4_wearable_no_sync"});
MATCH (a:Axis {id: "onto:saref/WellBeing"}), (r:AxisKnowledge {rule_id: "wb_r4_wearable_no_sync"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "smoke", condition: "smoke_detected == true", severity: "concern", immediate: true, rationale: "연기 감지는 시간 지연 없이 즉시 우려 상황으로 처리한다. 다른 규칙들과 달리 '몇 분 이상 지속' 같은 임계값을 두지 않는다 — 화재는 확산 속도가 빨라 지연 자체가 위험을 키운다.", source: "화재경보기 업계 표준 관행 (즉시 경보 원칙)", rule_id: "sf_r1_smoke_detected"});
MATCH (a:Axis {id: "onto:saref/Safety"}), (r:AxisKnowledge {rule_id: "sf_r1_smoke_detected"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "doorswitch", time_context: "day", threshold_minutes: 30, severity: "mild_concern", rationale: "주간에 현관문이 30분 이상 열려있으면 약한 우려로 취급한다. 상용 도어센서(ecobee 등)의 5분 기준보다 느슨하게 잡은 이유는, 낮에는 외출/배달/환기 등 정상적인 이유로 문을 오래 열어두는 경우가 흔해 오탐 위험이 크기 때문.", source: "ecobee Smart Security 'open reminder' 기본값(5분)을 가정 상황에 맞게 보수적으로 완화", rule_id: "sf_r2_door_open_day"});
MATCH (a:Axis {id: "onto:saref/Safety"}), (r:AxisKnowledge {rule_id: "sf_r2_door_open_day"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "doorswitch", time_context: "night", threshold_minutes: 5, severity: "concern", rationale: "야간에 현관문이 5분 이상 열려있으면 우려 상황으로 본다. 야간은 정상적으로 문을 열어둘 이유가 거의 없어 훨씬 민감하게(주간의 1/6 수준) 설정.", source: "YoLink 등 보안 목적 도어센서의 민감 설정 관행(1~2분)을 참고해 야간 기준을 주간보다 크게 낮춤", rule_id: "sf_r3_door_open_night"});
MATCH (a:Axis {id: "onto:saref/Safety"}), (r:AxisKnowledge {rule_id: "sf_r3_door_open_night"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "temperature", threshold_celsius: 18, direction: "below", severity: "concern", rationale: "실내 온도가 18°C 미만이면 우려 상황으로 본다. WHO 기준상 노인 취약군에는 20°C가 권장되지만, 오탐을 줄이기 위해 일반 인구 기준선인 18°C를 concern 임계값으로 삼고, 18~20°C 구간은 mild_concern으로 한 단계 낮춰 처리한다.", source: "WHO Housing and Health Guidelines (2018) 최소 18°C 권장", rule_id: "cf_r1_temp_too_low"});
MATCH (a:Axis {id: "onto:saref/Comfort"}), (r:AxisKnowledge {rule_id: "cf_r1_temp_too_low"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "temperature", threshold_celsius: 20, direction: "below", severity: "mild_concern", rationale: "18°C는 넘었지만 20°C 미만이면 약한 우려로 취급한다. 노인 등 취약군에 특화된 WHO 권장 최소 기준(20°C)에는 못 미치지만, 즉시 위험한 수준은 아니므로 concern보다 낮은 등급으로 처리해 오탐을 줄인다.", source: "WHO 취약군(노인 등) 권장 최소 온도 20°C", rule_id: "cf_r2_temp_mildly_low"});
MATCH (a:Axis {id: "onto:saref/Comfort"}), (r:AxisKnowledge {rule_id: "cf_r2_temp_mildly_low"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "temperature", time_context: "night", threshold_celsius: 18, direction: "below", severity: "concern", rationale: "야간에는 18°C 미만이면 즉시 concern으로 처리한다. 야간 저체온 노출이 혈압 상승 등 심혈관계에 더 크게 영향을 미친다는 연구 근거가 있어 야간 유지의 중요성을 별도로 강조.", source: "England Cold Weather Plan(2016) - 야간 18°C 유지 강조", rule_id: "cf_r3_temp_too_low_night"});
MATCH (a:Axis {id: "onto:saref/Comfort"}), (r:AxisKnowledge {rule_id: "cf_r3_temp_too_low_night"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);
CREATE (:AxisKnowledge {slot: "temperature", threshold_celsius: 28, direction: "above", severity: "concern", rationale: "실내 온도가 28°C를 초과하면 우려 상황으로 본다. 관련 임상연구에서 26°C를 노인 실내 온도 상한 기준으로 다루고 있으나 아직 확정된 공식 가이드라인이 아니라서, 여기서는 보수적으로 2°C 여유를 둔 28°C를 임계값으로 사용한다.", source: "노인 실내온도 상한 관련 임상연구(26°C 기준)를 보수적으로 조정", rule_id: "cf_r4_temp_too_high"});
MATCH (a:Axis {id: "onto:saref/Comfort"}), (r:AxisKnowledge {rule_id: "cf_r4_temp_too_high"}) CREATE (a)-[:HAS_AXIS_KNOWLEDGE]->(r);

// --- Axis -> Device ---
MATCH (a:Axis {id: "onto:saref/WellBeing"}), (d:Device {device_id: "cap:wearable_vitals"}) CREATE (a)-[:HAS_DEVICE]->(d);
MATCH (a:Axis {id: "onto:saref/WellBeing"}), (d:Device {device_id: "cap:motionsensor"}) CREATE (a)-[:HAS_DEVICE]->(d);
MATCH (a:Axis {id: "onto:saref/WellBeing"}), (d:Device {device_id: "cap:limo_robot_agent"}) CREATE (a)-[:HAS_DEVICE]->(d);
MATCH (a:Axis {id: "onto:saref/Safety"}), (d:Device {device_id: "cap:smokesensor"}) CREATE (a)-[:HAS_DEVICE]->(d);
MATCH (a:Axis {id: "onto:saref/Safety"}), (d:Device {device_id: "cap:doorswitch"}) CREATE (a)-[:HAS_DEVICE]->(d);
MATCH (a:Axis {id: "onto:saref/Safety"}), (d:Device {device_id: "cap:motionsensor"}) CREATE (a)-[:HAS_DEVICE]->(d);
MATCH (a:Axis {id: "onto:saref/Safety"}), (d:Device {device_id: "cap:limo_robot_agent"}) CREATE (a)-[:HAS_DEVICE]->(d);
MATCH (a:Axis {id: "onto:saref/Comfort"}), (d:Device {device_id: "cap:temperaturesensor"}) CREATE (a)-[:HAS_DEVICE]->(d);

// --- 검증 ---
MATCH (a:Axis) RETURN a.label, count{(a)-[:HAS_DEVICE]->()} AS devices, count{(a)-[:HAS_AXIS_KNOWLEDGE]->()} AS axis_rules;
MATCH (d:Device) RETURN d.device_id, count{(d)-[:HAS_FUNCTION]->()} AS functions, count{(d)-[:HAS_STATE]->()} AS states;