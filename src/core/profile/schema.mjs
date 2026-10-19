// Supported input shapes; profile.mjs retains semantic and effective-context validation.
const text = {type:'string',pattern:'\\S'};
const storedPath = {type:'string',minLength:1,description:'Absolute, ./ vault-relative, or ~/ home-relative path; runtime rejects traversal and applies host path semantics.'};
const binding = {type:'string',minLength:1,description:'Relative directory beneath the vault; runtime rejects absolute paths and empty, . or .. segments.'};
const email = {type:'string',pattern:'^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$'};
const templateNames = ['projectIndex','dailyPlan','milestone','task','planDayReview'];

const nullable = schema => ({...schema,type:[schema.type,'null']});

export const profileInputSchema = {
  type:'object',
  description:'Supported structural profile inputs. Runtime validation remains authoritative for timezone validity and host-specific path safety. Partial v2 preference layers do not establish a complete workspace; context resolution checks effective identity and bindings separately.',
  additionalProperties:false,
  required:['schema_version'],
  properties:{
    schema_version:{const:2},
    user:{type:'object',additionalProperties:false,properties:{
      name:text,email,
    }},
    timezone:nullable({...text,description:'IANA timezone name or system; runtime validates against the host timezone database.'}),
    priorities:nullable({type:'array',items:text}),
    templates:{type:'object',additionalProperties:false,properties:Object.fromEntries(templateNames.map(name =>
      [name,nullable({...storedPath,pattern:'\\.[mM][dD]$'})]))},
    projectIndex:{type:'object',additionalProperties:false,properties:{
      ttlSeconds:nullable({type:'integer',minimum:0,maximum:Number.MAX_SAFE_INTEGER}),
    }},
    sources:nullable({type:'object',additionalProperties:false,properties:{
      autoScan:{type:'boolean'},
      directories:{type:'array',items:{type:'string',minLength:1}},
      mcps:{type:'array',items:{type:'object',required:['name','tool'],additionalProperties:false,properties:{
        name:{type:'string',minLength:1},
        tool:{type:'string',minLength:1},
        params:{type:'object'},
      }}},
    }}),
    workspaceRoot:storedPath,
    vaultRoot:storedPath,
    projectsRoot:storedPath,
    dailyPlansRelative:binding,
  },
};

