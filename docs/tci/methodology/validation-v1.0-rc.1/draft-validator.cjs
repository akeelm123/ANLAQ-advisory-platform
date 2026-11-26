// Draft, isolated synthetic control model. No semantic extraction or scoring.
"use strict";
const spec=require("./TCI_Evidence_Validation_Specification_v1.0-rc.1.json");
const getRule=id=>spec.rules.find(r=>r.criterionId===id);
const out=(state,reason)=>({state,reason,scoringEligible:false,draft:true});
function assess(input){
 const rule=getRule(input?.criterionId);
 if(!rule)throw Error("Unknown criterion");
 // Materiality, evidence conclusions, independence, condition and applicability
 // are human assertions to be independently reviewed; never inferred by this model.
 if(input.applicability==="not_applicable")return out("exception_pending","Owner-approved exception and denominator rules required");
 if(input.applicability!=="applicable")return out("insufficient","Applicability unresolved");
 if(input.openMaterialContradiction===true)return out("contradiction","Investigate and preserve conflicting evidence");
 if(input.openMaterialContradiction!==false)return out("insufficient","Contradiction check missing");
 const allowed=new Set([...rule.primary,...rule.supplementary,...rule.conditional]);
 const refs=Array.isArray(input.refs)?input.refs:[];
 if(refs.some(r=>!r||!allowed.has(r.requestId)||!r.locator||!r.evidenceId))return out("insufficient","Invalid/missing mapped evidence reference");
 if(!refs.some(r=>rule.primary.includes(r.requestId))){
  // Only a mapped equivalent source is accepted in this conservative draft model.
  if(input.acceptedAlternative!==true||!refs.length||!input.alternativeRationale?.trim()||input.alternativeReviewerAccepted!==true)return out("insufficient","Primary or documented reviewer-accepted mapped equivalent required");
 }
 if(rule.conditional.length){
  if(input.conditionalApplies!==true&&input.conditionalApplies!==false)return out("insufficient","Conditional applicability unresolved");
  if(input.conditionalApplies===true&&!rule.conditional.every(id=>refs.some(r=>r.requestId===id)))return out("insufficient","Applicable conditional evidence missing");
  if(input.conditionalApplies===false&&!input.conditionalRationale?.trim())return out("insufficient","Out-of-scope rationale missing");
 }
 if(input.fieldsVerified!==true||input.comparable!==true)return out("insufficient","Extraction fields or comparable basis not confirmed");
 if(!["E1","E2"].includes(input.evidenceClass)||!["Strong","Moderate","Weak"].includes(input.evidenceStrength))return out("insufficient","Evidence support or separate strength unresolved");
 if(input.requiresCorroboration!==true&&input.requiresCorroboration!==false)return out("insufficient","Corroboration requirement not assessed");
 if(input.requiresCorroboration||input.evidenceClass==="E2"){
  if(new Set(refs.map(r=>r.evidenceId)).size<2||input.independenceConfirmed!==true)return out("insufficient","Independent corroboration not confirmed");
 }
 if(input.materialityReviewed!==true||!input.author?.trim()||!input.reviewer?.trim()||input.author.trim().toLowerCase()===input.reviewer.trim().toLowerCase()||input.reviewerAccepted!==true||!input.reviewReason?.trim())return out("review_pending","Independent human review required");
 if(input.condition==="met")return out("supported_met","Reviewer confirms condition is supported");
 if(input.condition==="not_met")return out("supported_not_met","Reviewer confirms adverse condition is supported");
 return out("insufficient","No supported condition judgement");
}
module.exports={spec,getRule,assess};
