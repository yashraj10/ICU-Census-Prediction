import { useState } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, Cell } from "recharts";

const DATA = {"summary":{"current_census":25,"status":"SAFE","pct_full":69.4,"capacity":36,"avg_arrivals":9.1,"avg_discharges":9.0,"tomorrow_arrivals_pred":53.4,"expected_discharges":6.9,"at_risk_days":32,"total_days":365},"census":[{"date":"2024-12-02","census":34,"arrivals":12,"discharges":11,"det_census":35,"expected_discharges":12.34841925458809,"pct_full":94.44444444444444,"status":"NEAR FULL"},{"date":"2024-12-03","census":37,"arrivals":13,"discharges":10,"det_census":38,"expected_discharges":9.809373163882658,"pct_full":102.77777777777776,"status":"AT RISK"},{"date":"2024-12-04","census":44,"arrivals":15,"discharges":8,"det_census":43,"expected_discharges":10.472824873725838,"pct_full":122.22222222222224,"status":"AT RISK"},{"date":"2024-12-05","census":39,"arrivals":7,"discharges":12,"det_census":41,"expected_discharges":9.048043168784051,"pct_full":108.33333333333331,"status":"AT RISK"},{"date":"2024-12-06","census":37,"arrivals":4,"discharges":6,"det_census":36,"expected_discharges":8.89263326832707,"pct_full":102.77777777777776,"status":"AT RISK"},{"date":"2024-12-07","census":33,"arrivals":8,"discharges":12,"det_census":35,"expected_discharges":9.296070622402254,"pct_full":91.66666666666666,"status":"NEAR FULL"},{"date":"2024-12-08","census":31,"arrivals":11,"discharges":13,"det_census":38,"expected_discharges":7.899998549346857,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2024-12-09","census":33,"arrivals":10,"discharges":8,"det_census":38,"expected_discharges":10.068827498333912,"pct_full":91.66666666666666,"status":"NEAR FULL"},{"date":"2024-12-10","census":31,"arrivals":8,"discharges":10,"det_census":37,"expected_discharges":8.716293014135811,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2024-12-11","census":30,"arrivals":10,"discharges":11,"det_census":38,"expected_discharges":8.972705701630797,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2024-12-12","census":33,"arrivals":6,"discharges":3,"det_census":37,"expected_discharges":7.364374202585381,"pct_full":91.66666666666666,"status":"NEAR FULL"},{"date":"2024-12-13","census":32,"arrivals":7,"discharges":8,"det_census":37,"expected_discharges":6.592489459858165,"pct_full":88.88888888888889,"status":"NEAR FULL"},{"date":"2024-12-14","census":32,"arrivals":8,"discharges":8,"det_census":37,"expected_discharges":7.577135928320154,"pct_full":88.88888888888889,"status":"NEAR FULL"},{"date":"2024-12-15","census":33,"arrivals":14,"discharges":13,"det_census":38,"expected_discharges":13.39278459961813,"pct_full":91.66666666666666,"status":"NEAR FULL"},{"date":"2024-12-16","census":35,"arrivals":14,"discharges":12,"det_census":42,"expected_discharges":10.08697398082226,"pct_full":97.2222222222222,"status":"AT RISK"},{"date":"2024-12-17","census":29,"arrivals":2,"discharges":8,"det_census":37,"expected_discharges":6.880294646597504,"pct_full":80.55555555555556,"status":"NEAR FULL"},{"date":"2024-12-18","census":34,"arrivals":13,"discharges":8,"det_census":41,"expected_discharges":8.579252754884166,"pct_full":94.44444444444444,"status":"NEAR FULL"},{"date":"2024-12-19","census":31,"arrivals":8,"discharges":11,"det_census":41,"expected_discharges":8.193829384159379,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2024-12-20","census":30,"arrivals":9,"discharges":10,"det_census":42,"expected_discharges":7.968783025126018,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2024-12-21","census":34,"arrivals":11,"discharges":7,"det_census":44,"expected_discharges":8.51834485696495,"pct_full":94.44444444444444,"status":"NEAR FULL"},{"date":"2024-12-22","census":30,"arrivals":7,"discharges":11,"det_census":41,"expected_discharges":10.312302672825645,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2024-12-23","census":30,"arrivals":11,"discharges":11,"det_census":42,"expected_discharges":10.246242977591026,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2024-12-24","census":24,"arrivals":7,"discharges":13,"det_census":38,"expected_discharges":10.54617292654004,"pct_full":66.66666666666666,"status":"SAFE"},{"date":"2024-12-25","census":25,"arrivals":6,"discharges":5,"det_census":37,"expected_discharges":7.431384570743031,"pct_full":69.44444444444444,"status":"SAFE"},{"date":"2024-12-26","census":34,"arrivals":13,"discharges":4,"det_census":40,"expected_discharges":9.94895245592066,"pct_full":94.44444444444444,"status":"NEAR FULL"},{"date":"2024-12-27","census":31,"arrivals":9,"discharges":12,"det_census":40,"expected_discharges":9.106018436386876,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2024-12-28","census":29,"arrivals":6,"discharges":8,"det_census":37,"expected_discharges":9.17625205441265,"pct_full":80.55555555555556,"status":"NEAR FULL"},{"date":"2024-12-29","census":32,"arrivals":11,"discharges":8,"det_census":37,"expected_discharges":10.960583260894412,"pct_full":88.88888888888889,"status":"NEAR FULL"},{"date":"2024-12-30","census":33,"arrivals":11,"discharges":10,"det_census":39,"expected_discharges":8.551371496245208,"pct_full":91.66666666666666,"status":"NEAR FULL"},{"date":"2024-12-31","census":29,"arrivals":6,"discharges":10,"det_census":34,"expected_discharges":10.670970775401116,"pct_full":80.55555555555556,"status":"NEAR FULL"},{"date":"2025-01-01","census":31,"arrivals":8,"discharges":6,"det_census":32,"expected_discharges":9.57328352199418,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2025-01-02","census":31,"arrivals":11,"discharges":11,"det_census":35,"expected_discharges":7.523424853326169,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2025-01-03","census":33,"arrivals":9,"discharges":7,"det_census":36,"expected_discharges":7.665906177346487,"pct_full":91.66666666666666,"status":"NEAR FULL"},{"date":"2025-01-04","census":30,"arrivals":6,"discharges":9,"det_census":35,"expected_discharges":6.913558081546615,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2025-01-05","census":26,"arrivals":6,"discharges":10,"det_census":34,"expected_discharges":7.099723016850144,"pct_full":72.22222222222221,"status":"SAFE"},{"date":"2025-01-06","census":30,"arrivals":15,"discharges":11,"det_census":38,"expected_discharges":11.26661395842612,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2025-01-07","census":23,"arrivals":4,"discharges":11,"det_census":33,"expected_discharges":8.708784068733266,"pct_full":63.888888888888886,"status":"SAFE"},{"date":"2025-01-08","census":27,"arrivals":9,"discharges":5,"det_census":35,"expected_discharges":7.015775736121117,"pct_full":75.0,"status":"SAFE"},{"date":"2025-01-09","census":27,"arrivals":5,"discharges":5,"det_census":33,"expected_discharges":7.1867405145947485,"pct_full":75.0,"status":"SAFE"},{"date":"2025-01-10","census":26,"arrivals":8,"discharges":9,"det_census":34,"expected_discharges":6.581845901375839,"pct_full":72.22222222222221,"status":"SAFE"},{"date":"2025-01-11","census":28,"arrivals":11,"discharges":9,"det_census":37,"expected_discharges":7.644990348269474,"pct_full":77.77777777777779,"status":"SAFE"},{"date":"2025-01-12","census":30,"arrivals":9,"discharges":7,"det_census":37,"expected_discharges":8.533758050249407,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2025-01-13","census":27,"arrivals":11,"discharges":14,"det_census":35,"expected_discharges":12.698046850168796,"pct_full":75.0,"status":"SAFE"},{"date":"2025-01-14","census":29,"arrivals":8,"discharges":6,"det_census":36,"expected_discharges":7.460959119716597,"pct_full":80.55555555555556,"status":"NEAR FULL"},{"date":"2025-01-15","census":31,"arrivals":13,"discharges":11,"det_census":40,"expected_discharges":9.026881235620664,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2025-01-16","census":30,"arrivals":6,"discharges":7,"det_census":34,"expected_discharges":11.62562580734208,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2025-01-17","census":31,"arrivals":9,"discharges":8,"det_census":36,"expected_discharges":7.145415255132605,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2025-01-18","census":29,"arrivals":3,"discharges":5,"det_census":32,"expected_discharges":6.631092980814296,"pct_full":80.55555555555556,"status":"NEAR FULL"},{"date":"2025-01-19","census":27,"arrivals":10,"discharges":12,"det_census":33,"expected_discharges":8.714160485324681,"pct_full":75.0,"status":"SAFE"},{"date":"2025-01-20","census":26,"arrivals":9,"discharges":10,"det_census":35,"expected_discharges":7.092576875613468,"pct_full":72.22222222222221,"status":"SAFE"},{"date":"2025-01-21","census":31,"arrivals":10,"discharges":5,"det_census":35,"expected_discharges":9.74927577919377,"pct_full":86.11111111111111,"status":"NEAR FULL"},{"date":"2025-01-22","census":32,"arrivals":10,"discharges":9,"det_census":37,"expected_discharges":8.005665708709524,"pct_full":88.88888888888889,"status":"NEAR FULL"},{"date":"2025-01-23","census":24,"arrivals":2,"discharges":10,"det_census":33,"expected_discharges":5.854992474131199,"pct_full":66.66666666666666,"status":"SAFE"},{"date":"2025-01-24","census":22,"arrivals":10,"discharges":12,"det_census":32,"expected_discharges":11.452477291279491,"pct_full":61.11111111111112,"status":"SAFE"},{"date":"2025-01-25","census":30,"arrivals":15,"discharges":7,"det_census":38,"expected_discharges":9.169170238122302,"pct_full":83.33333333333334,"status":"NEAR FULL"},{"date":"2025-01-26","census":26,"arrivals":5,"discharges":9,"det_census":36,"expected_discharges":7.305055541246884,"pct_full":72.22222222222221,"status":"SAFE"},{"date":"2025-01-27","census":28,"arrivals":11,"discharges":9,"det_census":36,"expected_discharges":11.396125684539196,"pct_full":77.77777777777779,"status":"SAFE"},{"date":"2025-01-28","census":26,"arrivals":6,"discharges":8,"det_census":34,"expected_discharges":8.366031823532616,"pct_full":72.22222222222221,"status":"SAFE"},{"date":"2025-01-29","census":23,"arrivals":3,"discharges":6,"det_census":32,"expected_discharges":5.373582374098186,"pct_full":63.888888888888886,"status":"SAFE"},{"date":"2025-01-30","census":25,"arrivals":8,"discharges":6,"det_census":33,"expected_discharges":6.917168913213764,"pct_full":69.44444444444444,"status":"SAFE"}],"arrivals_test":[{"date":"2025-01-17","actual":43,"rf_pred":61.95735526502658,"gb_pred":69.53406122192116,"ensemble_pred":65.74570824347387},{"date":"2025-01-18","actual":59,"rf_pred":57.03216264780461,"gb_pred":57.14472020505975,"ensemble_pred":57.088441426432176},{"date":"2025-01-19","actual":50,"rf_pred":48.21121788411031,"gb_pred":51.63096827920996,"ensemble_pred":49.92109308166013},{"date":"2025-01-20","actual":51,"rf_pred":57.96681979165896,"gb_pred":60.33600267960047,"ensemble_pred":59.15141123562971},{"date":"2025-01-21","actual":58,"rf_pred":56.8868589669324,"gb_pred":58.02606605067425,"ensemble_pred":57.45646250880333},{"date":"2025-01-22","actual":69,"rf_pred":57.56172608493791,"gb_pred":54.17483186236512,"ensemble_pred":55.86827897365151},{"date":"2025-01-23","actual":50,"rf_pred":55.73040143360196,"gb_pred":54.188614478594246,"ensemble_pred":54.95950795609811},{"date":"2025-01-24","actual":65,"rf_pred":57.35092968408687,"gb_pred":56.68035789486468,"ensemble_pred":57.015643789475774},{"date":"2025-01-25","actual":61,"rf_pred":57.04900136730467,"gb_pred":57.97102719393684,"ensemble_pred":57.51001428062075},{"date":"2025-01-26","actual":44,"rf_pred":49.802280500772426,"gb_pred":48.547378173041736,"ensemble_pred":49.17482933690708},{"date":"2025-01-27","actual":65,"rf_pred":58.3452215060848,"gb_pred":55.93881749207108,"ensemble_pred":57.14201949907794},{"date":"2025-01-28","actual":57,"rf_pred":57.45031612456104,"gb_pred":54.918685191068576,"ensemble_pred":56.18450065781481},{"date":"2025-01-29","actual":62,"rf_pred":61.3735527445217,"gb_pred":66.90585090651459,"ensemble_pred":64.13970182551815},{"date":"2025-01-30","actual":67,"rf_pred":56.18576962479256,"gb_pred":50.67398824215921,"ensemble_pred":53.42987893347589}],"daily_loc":[{"date":"2024-12-02","arrivals_ICU":12,"arrivals_Med_Surg":21,"arrivals_Other":11,"arrivals_PCU":4,"arrivals_Tele":7,"total_arrivals":55},{"date":"2024-12-03","arrivals_ICU":13,"arrivals_Med_Surg":35,"arrivals_Other":10,"arrivals_PCU":5,"arrivals_Tele":8,"total_arrivals":71},{"date":"2024-12-04","arrivals_ICU":15,"arrivals_Med_Surg":26,"arrivals_Other":7,"arrivals_PCU":6,"arrivals_Tele":2,"total_arrivals":56},{"date":"2024-12-05","arrivals_ICU":7,"arrivals_Med_Surg":27,"arrivals_Other":12,"arrivals_PCU":4,"arrivals_Tele":8,"total_arrivals":58},{"date":"2024-12-06","arrivals_ICU":4,"arrivals_Med_Surg":27,"arrivals_Other":12,"arrivals_PCU":5,"arrivals_Tele":3,"total_arrivals":51},{"date":"2024-12-07","arrivals_ICU":8,"arrivals_Med_Surg":29,"arrivals_Other":12,"arrivals_PCU":1,"arrivals_Tele":8,"total_arrivals":58},{"date":"2024-12-08","arrivals_ICU":11,"arrivals_Med_Surg":19,"arrivals_Other":13,"arrivals_PCU":4,"arrivals_Tele":4,"total_arrivals":51},{"date":"2024-12-09","arrivals_ICU":10,"arrivals_Med_Surg":32,"arrivals_Other":9,"arrivals_PCU":9,"arrivals_Tele":4,"total_arrivals":64},{"date":"2024-12-10","arrivals_ICU":8,"arrivals_Med_Surg":33,"arrivals_Other":12,"arrivals_PCU":4,"arrivals_Tele":5,"total_arrivals":62},{"date":"2024-12-11","arrivals_ICU":10,"arrivals_Med_Surg":25,"arrivals_Other":11,"arrivals_PCU":4,"arrivals_Tele":7,"total_arrivals":57},{"date":"2024-12-12","arrivals_ICU":6,"arrivals_Med_Surg":28,"arrivals_Other":16,"arrivals_PCU":10,"arrivals_Tele":10,"total_arrivals":70},{"date":"2024-12-13","arrivals_ICU":7,"arrivals_Med_Surg":36,"arrivals_Other":9,"arrivals_PCU":11,"arrivals_Tele":7,"total_arrivals":70},{"date":"2024-12-14","arrivals_ICU":8,"arrivals_Med_Surg":37,"arrivals_Other":11,"arrivals_PCU":2,"arrivals_Tele":6,"total_arrivals":64},{"date":"2024-12-15","arrivals_ICU":14,"arrivals_Med_Surg":16,"arrivals_Other":10,"arrivals_PCU":2,"arrivals_Tele":4,"total_arrivals":46},{"date":"2024-12-16","arrivals_ICU":14,"arrivals_Med_Surg":12,"arrivals_Other":12,"arrivals_PCU":4,"arrivals_Tele":9,"total_arrivals":51},{"date":"2024-12-17","arrivals_ICU":2,"arrivals_Med_Surg":23,"arrivals_Other":18,"arrivals_PCU":5,"arrivals_Tele":5,"total_arrivals":53},{"date":"2024-12-18","arrivals_ICU":13,"arrivals_Med_Surg":27,"arrivals_Other":10,"arrivals_PCU":4,"arrivals_Tele":7,"total_arrivals":61},{"date":"2024-12-19","arrivals_ICU":8,"arrivals_Med_Surg":37,"arrivals_Other":8,"arrivals_PCU":6,"arrivals_Tele":5,"total_arrivals":64},{"date":"2024-12-20","arrivals_ICU":9,"arrivals_Med_Surg":24,"arrivals_Other":14,"arrivals_PCU":8,"arrivals_Tele":7,"total_arrivals":62},{"date":"2024-12-21","arrivals_ICU":11,"arrivals_Med_Surg":23,"arrivals_Other":17,"arrivals_PCU":5,"arrivals_Tele":7,"total_arrivals":63},{"date":"2024-12-22","arrivals_ICU":7,"arrivals_Med_Surg":32,"arrivals_Other":9,"arrivals_PCU":3,"arrivals_Tele":1,"total_arrivals":52},{"date":"2024-12-23","arrivals_ICU":11,"arrivals_Med_Surg":18,"arrivals_Other":13,"arrivals_PCU":3,"arrivals_Tele":5,"total_arrivals":50},{"date":"2024-12-24","arrivals_ICU":7,"arrivals_Med_Surg":29,"arrivals_Other":22,"arrivals_PCU":3,"arrivals_Tele":5,"total_arrivals":66},{"date":"2024-12-25","arrivals_ICU":6,"arrivals_Med_Surg":27,"arrivals_Other":8,"arrivals_PCU":4,"arrivals_Tele":6,"total_arrivals":51},{"date":"2024-12-26","arrivals_ICU":13,"arrivals_Med_Surg":34,"arrivals_Other":6,"arrivals_PCU":2,"arrivals_Tele":5,"total_arrivals":60},{"date":"2024-12-27","arrivals_ICU":9,"arrivals_Med_Surg":34,"arrivals_Other":17,"arrivals_PCU":8,"arrivals_Tele":4,"total_arrivals":72},{"date":"2024-12-28","arrivals_ICU":6,"arrivals_Med_Surg":26,"arrivals_Other":13,"arrivals_PCU":5,"arrivals_Tele":8,"total_arrivals":58},{"date":"2024-12-29","arrivals_ICU":11,"arrivals_Med_Surg":27,"arrivals_Other":11,"arrivals_PCU":4,"arrivals_Tele":5,"total_arrivals":58},{"date":"2024-12-30","arrivals_ICU":11,"arrivals_Med_Surg":24,"arrivals_Other":17,"arrivals_PCU":2,"arrivals_Tele":3,"total_arrivals":57},{"date":"2024-12-31","arrivals_ICU":6,"arrivals_Med_Surg":20,"arrivals_Other":14,"arrivals_PCU":3,"arrivals_Tele":8,"total_arrivals":51},{"date":"2025-01-01","arrivals_ICU":8,"arrivals_Med_Surg":22,"arrivals_Other":8,"arrivals_PCU":4,"arrivals_Tele":4,"total_arrivals":46},{"date":"2025-01-02","arrivals_ICU":11,"arrivals_Med_Surg":21,"arrivals_Other":19,"arrivals_PCU":7,"arrivals_Tele":9,"total_arrivals":67},{"date":"2025-01-03","arrivals_ICU":9,"arrivals_Med_Surg":27,"arrivals_Other":16,"arrivals_PCU":3,"arrivals_Tele":2,"total_arrivals":57},{"date":"2025-01-04","arrivals_ICU":6,"arrivals_Med_Surg":26,"arrivals_Other":18,"arrivals_PCU":4,"arrivals_Tele":10,"total_arrivals":64},{"date":"2025-01-05","arrivals_ICU":6,"arrivals_Med_Surg":9,"arrivals_Other":7,"arrivals_PCU":7,"arrivals_Tele":4,"total_arrivals":33},{"date":"2025-01-06","arrivals_ICU":15,"arrivals_Med_Surg":14,"arrivals_Other":11,"arrivals_PCU":7,"arrivals_Tele":6,"total_arrivals":53},{"date":"2025-01-07","arrivals_ICU":4,"arrivals_Med_Surg":28,"arrivals_Other":12,"arrivals_PCU":3,"arrivals_Tele":4,"total_arrivals":51},{"date":"2025-01-08","arrivals_ICU":9,"arrivals_Med_Surg":30,"arrivals_Other":9,"arrivals_PCU":4,"arrivals_Tele":7,"total_arrivals":59},{"date":"2025-01-09","arrivals_ICU":5,"arrivals_Med_Surg":29,"arrivals_Other":20,"arrivals_PCU":2,"arrivals_Tele":11,"total_arrivals":67},{"date":"2025-01-10","arrivals_ICU":8,"arrivals_Med_Surg":31,"arrivals_Other":18,"arrivals_PCU":7,"arrivals_Tele":5,"total_arrivals":69},{"date":"2025-01-11","arrivals_ICU":11,"arrivals_Med_Surg":21,"arrivals_Other":14,"arrivals_PCU":3,"arrivals_Tele":7,"total_arrivals":56},{"date":"2025-01-12","arrivals_ICU":9,"arrivals_Med_Surg":29,"arrivals_Other":9,"arrivals_PCU":3,"arrivals_Tele":5,"total_arrivals":55},{"date":"2025-01-13","arrivals_ICU":11,"arrivals_Med_Surg":24,"arrivals_Other":11,"arrivals_PCU":4,"arrivals_Tele":3,"total_arrivals":53},{"date":"2025-01-14","arrivals_ICU":8,"arrivals_Med_Surg":24,"arrivals_Other":14,"arrivals_PCU":3,"arrivals_Tele":1,"total_arrivals":50},{"date":"2025-01-15","arrivals_ICU":13,"arrivals_Med_Surg":32,"arrivals_Other":15,"arrivals_PCU":5,"arrivals_Tele":6,"total_arrivals":71},{"date":"2025-01-16","arrivals_ICU":6,"arrivals_Med_Surg":21,"arrivals_Other":6,"arrivals_PCU":5,"arrivals_Tele":7,"total_arrivals":45},{"date":"2025-01-17","arrivals_ICU":9,"arrivals_Med_Surg":18,"arrivals_Other":6,"arrivals_PCU":2,"arrivals_Tele":8,"total_arrivals":43},{"date":"2025-01-18","arrivals_ICU":3,"arrivals_Med_Surg":36,"arrivals_Other":11,"arrivals_PCU":4,"arrivals_Tele":5,"total_arrivals":59},{"date":"2025-01-19","arrivals_ICU":10,"arrivals_Med_Surg":26,"arrivals_Other":9,"arrivals_PCU":3,"arrivals_Tele":2,"total_arrivals":50},{"date":"2025-01-20","arrivals_ICU":9,"arrivals_Med_Surg":20,"arrivals_Other":12,"arrivals_PCU":4,"arrivals_Tele":6,"total_arrivals":51},{"date":"2025-01-21","arrivals_ICU":10,"arrivals_Med_Surg":24,"arrivals_Other":20,"arrivals_PCU":1,"arrivals_Tele":3,"total_arrivals":58},{"date":"2025-01-22","arrivals_ICU":10,"arrivals_Med_Surg":34,"arrivals_Other":10,"arrivals_PCU":4,"arrivals_Tele":11,"total_arrivals":69},{"date":"2025-01-23","arrivals_ICU":2,"arrivals_Med_Surg":26,"arrivals_Other":11,"arrivals_PCU":7,"arrivals_Tele":4,"total_arrivals":50},{"date":"2025-01-24","arrivals_ICU":10,"arrivals_Med_Surg":31,"arrivals_Other":11,"arrivals_PCU":7,"arrivals_Tele":6,"total_arrivals":65},{"date":"2025-01-25","arrivals_ICU":15,"arrivals_Med_Surg":34,"arrivals_Other":4,"arrivals_PCU":3,"arrivals_Tele":5,"total_arrivals":61},{"date":"2025-01-26","arrivals_ICU":5,"arrivals_Med_Surg":26,"arrivals_Other":9,"arrivals_PCU":1,"arrivals_Tele":3,"total_arrivals":44},{"date":"2025-01-27","arrivals_ICU":11,"arrivals_Med_Surg":27,"arrivals_Other":16,"arrivals_PCU":6,"arrivals_Tele":5,"total_arrivals":65},{"date":"2025-01-28","arrivals_ICU":6,"arrivals_Med_Surg":32,"arrivals_Other":11,"arrivals_PCU":3,"arrivals_Tele":5,"total_arrivals":57},{"date":"2025-01-29","arrivals_ICU":3,"arrivals_Med_Surg":39,"arrivals_Other":11,"arrivals_PCU":3,"arrivals_Tele":6,"total_arrivals":62},{"date":"2025-01-30","arrivals_ICU":8,"arrivals_Med_Surg":30,"arrivals_Other":15,"arrivals_PCU":7,"arrivals_Tele":7,"total_arrivals":67}],"los_stats":{"ICU":{"count":6422,"mean":4.4,"median":2.0,"short_pct":53.6,"extended_pct":5.2},"Med_Surg":{"count":4252,"mean":7.0,"median":3.0,"short_pct":44.8,"extended_pct":10.7},"PCU":{"count":823,"mean":5.7,"median":3.0,"short_pct":44.1,"extended_pct":8.4},"Tele":{"count":424,"mean":2.8,"median":2.0,"short_pct":59.2,"extended_pct":0.9}},"hazard":[{"day":1,"hazard":0.3223},{"day":2,"hazard":0.3153},{"day":3,"hazard":0.2591},{"day":4,"hazard":0.2382},{"day":5,"hazard":0.2105},{"day":6,"hazard":0.1837},{"day":7,"hazard":0.1522},{"day":8,"hazard":0.1545},{"day":9,"hazard":0.1416},{"day":10,"hazard":0.1469},{"day":11,"hazard":0.1511},{"day":12,"hazard":0.0994},{"day":13,"hazard":0.131},{"day":14,"hazard":0.1164},{"day":15,"hazard":0.1168},{"day":16,"hazard":0.1085},{"day":17,"hazard":0.1065},{"day":18,"hazard":0.1277},{"day":19,"hazard":0.0537},{"day":20,"hazard":0.0722},{"day":21,"hazard":0.0833},{"day":22,"hazard":0.1212},{"day":23,"hazard":0.0828},{"day":24,"hazard":0.0526},{"day":25,"hazard":0.0556},{"day":26,"hazard":0.084},{"day":27,"hazard":0.1193},{"day":28,"hazard":0.0938},{"day":29,"hazard":0.046}]};

const StatusBadge = ({ status }) => {
  const colors = {
    SAFE: { bg: "#059669", text: "#ecfdf5" },
    "NEAR FULL": { bg: "#d97706", text: "#fffbeb" },
    "AT RISK": { bg: "#dc2626", text: "#fef2f2" },
  };
  const c = colors[status] || colors.SAFE;
  return (
    <span style={{ background: c.bg, color: c.text, padding: "4px 14px", borderRadius: "6px", fontWeight: 700, fontSize: 13, letterSpacing: "0.5px" }}>
      {status}
    </span>
  );
};

const Card = ({ children, title, span = 1 }) => (
  <div style={{
    background: "#1a1f2e",
    borderRadius: 14,
    padding: "22px 24px",
    border: "1px solid rgba(255,255,255,0.06)",
    gridColumn: span > 1 ? `span ${span}` : undefined,
    boxShadow: "0 4px 24px rgba(0,0,0,0.2)"
  }}>
    {title && <h3 style={{ margin: "0 0 16px", fontSize: 15, fontWeight: 600, color: "#94a3b8", letterSpacing: "0.3px" }}>{title}</h3>}
    {children}
  </div>
);

const Metric = ({ label, value, unit, color = "#e2e8f0", sub }) => (
  <div style={{ textAlign: "center" }}>
    <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4, fontWeight: 500 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color, lineHeight: 1.1 }}>
      {value}<span style={{ fontSize: 14, fontWeight: 400, marginLeft: 2 }}>{unit}</span>
    </div>
    {sub && <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{sub}</div>}
  </div>
);

const formatDate = (d) => {
  const date = new Date(d);
  return `${date.getMonth()+1}/${date.getDate()}`;
};

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("census");
  const { summary: s, census, arrivals_test, daily_loc, los_stats, hazard } = DATA;

  const censusData = census.map(d => ({
    ...d,
    date: formatDate(d.date),
    capacity: s.capacity,
    threshold80: Math.round(s.capacity * 0.8),
  }));

  const arrData = arrivals_test.map(d => ({
    ...d,
    date: formatDate(d.date),
    actual: Math.round(d.actual),
    rf: Math.round(d.rf_pred * 10) / 10,
    gb: Math.round(d.gb_pred * 10) / 10,
    ensemble: Math.round(d.ensemble_pred * 10) / 10,
  }));

  const locData = daily_loc.map(d => ({
    date: formatDate(d.date),
    ICU: d.arrivals_ICU || 0,
    Med_Surg: d.arrivals_Med_Surg || 0,
    PCU: d.arrivals_PCU || 0,
    Tele: d.arrivals_Tele || 0,
    Total: d.total_arrivals || 0,
  }));

  const statusCounts = { SAFE: 0, "NEAR FULL": 0, "AT RISK": 0 };
  census.forEach(d => { if (statusCounts[d.status] !== undefined) statusCounts[d.status]++; });
  const statusData = Object.entries(statusCounts).map(([name, value]) => ({ name, value }));
  const statusColors = { SAFE: "#059669", "NEAR FULL": "#d97706", "AT RISK": "#dc2626" };

  const tabs = [
    { id: "census", label: "ICU Census" },
    { id: "arrivals", label: "Arrivals" },
    { id: "los", label: "LOS & Discharge" },
  ];

  return (
    <div style={{
      background: "linear-gradient(135deg, #0f1218 0%, #151b28 50%, #0f1218 100%)",
      minHeight: "100vh",
      color: "#e2e8f0",
      fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
      padding: "24px",
    }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: 28, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0, letterSpacing: "-0.5px", background: "linear-gradient(90deg, #60a5fa, #34d399)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              ICU Capacity Dashboard
            </h1>
            <p style={{ color: "#64748b", fontSize: 13, margin: "4px 0 0" }}>
              Predicting Census with Arrivals, LOS & Discharge Modeling
            </p>
          </div>
          <StatusBadge status={s.status} />
        </div>

        {/* KPI Row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 14, marginBottom: 22 }}>
          <Card>
            <Metric label="Current Census" value={s.current_census} unit={`/${s.capacity}`} color={s.pct_full > 95 ? "#ef4444" : s.pct_full > 80 ? "#f59e0b" : "#34d399"} sub={`${s.pct_full}% full`} />
          </Card>
          <Card>
            <Metric label="Avg Daily Arrivals" value={s.avg_arrivals} unit="/day" color="#60a5fa" />
          </Card>
          <Card>
            <Metric label="Avg Discharges" value={s.avg_discharges} unit="/day" color="#a78bfa" />
          </Card>
          <Card>
            <Metric label="Expected Disch." value={s.expected_discharges} unit="tmrw" color="#fb923c" />
          </Card>
          <Card>
            <Metric label="At Risk Days" value={s.at_risk_days} unit={`/${s.total_days}`} color="#ef4444" sub={`${(s.at_risk_days/s.total_days*100).toFixed(1)}% of year`} />
          </Card>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 4, marginBottom: 18, background: "#1a1f2e", borderRadius: 10, padding: 4, width: "fit-content" }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              padding: "8px 20px", borderRadius: 8, border: "none", cursor: "pointer", fontSize: 13, fontWeight: 600,
              background: activeTab === t.id ? "#2563eb" : "transparent",
              color: activeTab === t.id ? "#fff" : "#64748b",
              transition: "all 0.2s"
            }}>
              {t.label}
            </button>
          ))}
        </div>

        {/* Census Tab */}
        {activeTab === "census" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card title="ICU Census Over Time (Last 60 Days)" span={2}>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={censusData}>
                  <defs>
                    <linearGradient id="censusFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} interval={6} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }} />
                  <Area type="monotone" dataKey="census" stroke="#3b82f6" fill="url(#censusFill)" strokeWidth={2} name="Census" />
                  <Line type="monotone" dataKey="capacity" stroke="#ef4444" strokeDasharray="6 4" strokeWidth={1.5} dot={false} name="Capacity" />
                  <Line type="monotone" dataKey="threshold80" stroke="#f59e0b" strokeDasharray="4 4" strokeWidth={1} dot={false} name="80% Threshold" />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Daily Arrivals vs Discharges">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={censusData.filter((_, i) => i % 2 === 0)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} interval={4} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="arrivals" fill="#60a5fa" name="Arrivals" radius={[3,3,0,0]} />
                  <Bar dataKey="discharges" fill="#a78bfa" name="Discharges" radius={[3,3,0,0]} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Capacity Status (Last 60 Days)">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={statusData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#94a3b8" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="value" radius={[6,6,0,0]} name="Days">
                    {statusData.map((d, i) => (
                      <Cell key={i} fill={statusColors[d.name] || "#64748b"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}

        {/* Arrivals Tab */}
        {activeTab === "arrivals" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card title="Arrival Forecast (14-Day Holdout)" span={2}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={arrData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="actual" stroke="#e2e8f0" strokeWidth={2.5} dot={{ r: 4 }} name="Actual" />
                  <Line type="monotone" dataKey="rf" stroke="#34d399" strokeDasharray="5 5" strokeWidth={1.5} dot={{ r: 3 }} name="Random Forest" />
                  <Line type="monotone" dataKey="gb" stroke="#fb923c" strokeDasharray="5 5" strokeWidth={1.5} dot={{ r: 3 }} name="Gradient Boosting" />
                  <Line type="monotone" dataKey="ensemble" stroke="#a78bfa" strokeWidth={2} dot={{ r: 3 }} name="Ensemble" />
                </LineChart>
              </ResponsiveContainer>
            </Card>
            <Card title="Arrivals by Level of Care (Last 60 Days)" span={2}>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={locData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#64748b" }} interval={6} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Area type="monotone" dataKey="Med_Surg" stackId="1" fill="#34d399" stroke="#34d399" fillOpacity={0.6} name="Med/Surg" />
                  <Area type="monotone" dataKey="ICU" stackId="1" fill="#3b82f6" stroke="#3b82f6" fillOpacity={0.6} name="ICU" />
                  <Area type="monotone" dataKey="PCU" stackId="1" fill="#fb923c" stroke="#fb923c" fillOpacity={0.6} name="PCU" />
                  <Area type="monotone" dataKey="Tele" stackId="1" fill="#a78bfa" stroke="#a78bfa" fillOpacity={0.6} name="Tele" />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}

        {/* LOS Tab */}
        {activeTab === "los" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card title="ICU Discharge Hazard by Day" span={2}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={hazard}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: "#64748b" }} label={{ value: "ICU Day", position: "insideBottom", offset: -2, style: { fill: "#64748b", fontSize: 11 } }} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickFormatter={v => `${(v*100).toFixed(0)}%`} />
                  <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }} formatter={v => `${(v*100).toFixed(1)}%`} />
                  <Bar dataKey="hazard" fill="#3b82f6" radius={[3,3,0,0]} name="P(Discharge)">
                    {hazard.map((d, i) => (
                      <Cell key={i} fill={d.hazard > 0.25 ? "#34d399" : d.hazard > 0.15 ? "#60a5fa" : "#f59e0b"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card title="LOS Statistics by Unit" span={2}>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
                {Object.entries(los_stats).map(([unit, st]) => {
                  const unitColors = { ICU: "#3b82f6", Med_Surg: "#34d399", PCU: "#fb923c", Tele: "#a78bfa" };
                  const labels = { ICU: "ICU", Med_Surg: "Med/Surg", PCU: "PCU", Tele: "Telemetry" };
                  return (
                    <div key={unit} style={{ background: "#111827", borderRadius: 10, padding: 16, border: `1px solid ${unitColors[unit]}33` }}>
                      <div style={{ fontSize: 14, fontWeight: 700, color: unitColors[unit], marginBottom: 10 }}>{labels[unit]}</div>
                      <div style={{ fontSize: 11, color: "#94a3b8", lineHeight: 2 }}>
                        <div>Patients: <strong style={{ color: "#e2e8f0" }}>{st.count.toLocaleString()}</strong></div>
                        <div>Mean LOS: <strong style={{ color: "#e2e8f0" }}>{st.mean}d</strong></div>
                        <div>Median LOS: <strong style={{ color: "#e2e8f0" }}>{st.median}d</strong></div>
                        <div>Short (≤2d): <strong style={{ color: "#34d399" }}>{st.short_pct}%</strong></div>
                        <div>Extended ({">"}14d): <strong style={{ color: "#ef4444" }}>{st.extended_pct}%</strong></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
            <Card title="Model Performance Summary" span={2}>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #334155" }}>
                      {["Model", "Task", "MAE", "R²", "AUC", "F1"].map(h => (
                        <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: "#64748b", fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { m: "RF (Total Arrivals)", t: "Regression", mae: "5.99", r2: "0.073", auc: "—", f1: "—" },
                      { m: "GB (Total Arrivals)", t: "Regression", mae: "7.62", r2: "-0.649", auc: "—", f1: "—" },
                      { m: "GB (ICU Short-Stay)", t: "Classification", mae: "—", r2: "—", auc: "0.935", f1: "0.853" },
                      { m: "LR (ICU Short-Stay)", t: "Classification", mae: "—", r2: "—", auc: "0.879", f1: "0.806" },
                      { m: "GB (PCU Short-Stay)", t: "Classification", mae: "—", r2: "—", auc: "0.709", f1: "0.586" },
                      { m: "GB (Tele Short-Stay)", t: "Classification", mae: "—", r2: "—", auc: "0.756", f1: "0.704" },
                    ].map((r, i) => (
                      <tr key={i} style={{ borderBottom: "1px solid #1e293b" }}>
                        <td style={{ padding: "8px 12px", fontWeight: 500 }}>{r.m}</td>
                        <td style={{ padding: "8px 12px", color: "#94a3b8" }}>{r.t}</td>
                        <td style={{ padding: "8px 12px" }}>{r.mae}</td>
                        <td style={{ padding: "8px 12px", color: r.r2.startsWith("-") ? "#ef4444" : "#34d399" }}>{r.r2}</td>
                        <td style={{ padding: "8px 12px", color: r.auc !== "—" ? "#60a5fa" : "#475569" }}>{r.auc}</td>
                        <td style={{ padding: "8px 12px" }}>{r.f1}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
