# Evidence Validation Specification v1.0 RC.1

Review candidate tied to the approved Master Evidence Register commit and SHA-256 in the JSON specification. The workbook is the review artifact, JSON is the machine-readable draft specification, draft-validator.cjs is an isolated synthetic structural control reference, and TEST-RESULTS.txt records automated test output. No code in this folder issues scores or executive assessments.

Run `node --test draft-validator.test.cjs` locally. The 112 synthetic fixtures assert explicitly supplied structured conditions; their written examples have not been semantically validated against documents. The 121 passing tests show structural gates, not AI extraction accuracy, evidence authenticity, security or a release approval.

Review the criterion rules, mapping requirements, global rules and scenario examples. Review the accompanying secure evidence handling design separately. Scoring, live client data and deployment remain locked until their own approval and implementation/test gates.
