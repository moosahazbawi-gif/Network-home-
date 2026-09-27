const express=require("express");
const { requireAuth, requireRole, requireCsrf }=require("./middleware/auth");
const app=express();
app.use(express.json({limit:"32kb"}));
const PANTHER_URL=process.env.PANTHER_URL||"http://127.0.0.1:8787";
let pantherUrl;
try{pantherUrl=new URL(PANTHER_URL);if(!["http:","https:"].includes(pantherUrl.protocol))throw new Error();}catch{throw new Error("Invalid PANTHER_URL");}
app.get("/api/panther/health",requireAuth,async(_req,res)=>{try{const r=await fetch(new URL("/health",pantherUrl));res.status(r.status).json(await r.json());}catch{res.status(503).json({ok:false,error:"Panther unavailable"});}});
app.post("/api/panther/chat",requireRole("admin"),requireCsrf,async(req,res)=>{const prompt=typeof req.body?.prompt==="string"?req.body.prompt.trim():"";if(!prompt||prompt.length>12000)return res.status(400).json({ok:false,error:"prompt is required and must be <= 12000 characters"});try{const r=await fetch(new URL("/chat",pantherUrl),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt}),signal:AbortSignal.timeout(30000)});res.status(r.status).json(await r.json());}catch{res.status(503).json({ok:false,error:"Panther unavailable"});}});
module.exports=app;