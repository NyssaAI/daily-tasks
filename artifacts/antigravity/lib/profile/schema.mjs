// Supported input shapes; profile.mjs retains semantic and effective-context validation.
const text = {type:'string',pattern:'\\S'};
const storedPath = {type:'string',minLength:1,description:'Absolute, ./ vault-relative, or ~/ home-relative path; runtime rejects traversal and applies host path semantics.'};
const binding = {type:'string',minLength:1,description:'Relative directory beneath the vault; runtime rejects absolute paths and empty, . or .. segments.'};
const email = {type:'string',pattern:'^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$'};
const templateNames = ['projectIndex','dailyPlan','milestone','task','planDayReview'];

function profileBranch(version) {
  const layer = version === 2;
  const nullable = schema => layer ? {...schema,type:[schema.type,'null']} : schema;
  return {
    type:'object',
    ...(layer ? {additionalProperties:false} : {}),
    required:layer ? ['schema_version'] : ['schema_version','user','timezone','priorities','vaultRoot','projectsRoot','dailyPlansRelative'],
    properties:{
      schema_version:{const:version},
      user:{type:'object',...(layer ? {additionalProperties:false} : {required:['name','email']}),properties:{
        name:layer ? text : {type:'string',minLength:1},email,
      }},
      timezone:nullable({...text,description:'IANA timezone name or system; runtime validates against the host timezone database.'}),
      priorities:nullable({type:'array',items:text}),
      templates:{type:'object',additionalProperties:false,properties:Object.fromEntries(templateNames.map(name =>
        [name,nullable({...storedPath,pattern:'\\.[mM][dD]$'})]))},
      projectIndex:{type:'object',additionalProperties:false,...(layer ? {} : {required:['ttlSeconds']}),properties:{
        ttlSeconds:nullable({type:'integer',minimum:0,maximum:Number.MAX_SAFE_INTEGER}),
      }},
      vaultRoot:storedPath,
      projectsRoot:storedPath,
      dailyPlansRelative:binding,
    },
  };
}

export const profileInputSchema = {
  type:'object',
  description:'Supported structural profile inputs. Runtime validation remains authoritative for timezone validity and host-specific path safety. Partial v2 preference layers do not establish a complete workspace; context resolution checks effective identity and bindings separately.',
  oneOf:[profileBranch(1),profileBranch(2)],
};
