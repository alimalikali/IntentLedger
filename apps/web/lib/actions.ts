"use server";
import {revalidatePath} from "next/cache";
const base=process.env.API_URL??"http://127.0.0.1:8000";
async function post(path:string,body:unknown){const token=process.env.LOCAL_API_TOKEN;const response=await fetch(`${base}/api/v1${path}`,{method:"POST",headers:{"content-type":"application/json",...(token?{authorization:`Bearer ${token}`}:{})},body:JSON.stringify(body),cache:"no-store"});if(!response.ok)throw new Error(`${response.status}: ${await response.text()}`);return response.json()}
export async function registerRepository(form:FormData){await post("/repositories",{path:String(form.get("path")),display_name:String(form.get("display_name")||"")||null});revalidatePath("/")}
export async function ingestRepository(form:FormData){const rule=JSON.parse(String(form.get("rule")));await post(`/repositories/${form.get("repository_id")}/ingestions`,{revision:String(form.get("revision")||"HEAD"),rule});revalidatePath("/")}
export async function createAnalysis(form:FormData){await post("/analyses",{repository_id:String(form.get("repository_id")),base:String(form.get("base")),head:String(form.get("head")),evidence_cutoff:new Date(String(form.get("evidence_cutoff"))).toISOString(),mode:"strict_replay",idempotency_key:crypto.randomUUID()});revalidatePath("/")}
export async function reviewRule(form:FormData){await post("/reviews",{target_id:String(form.get("target_id")),version:Number(form.get("version")),content_hash:String(form.get("content_hash")),action:String(form.get("action")),reviewer:"local-reviewer",rationale:String(form.get("rationale")),idempotency_key:crypto.randomUUID()});revalidatePath("/rules")}
export async function resumeAnalysis(form:FormData){await post(`/analyses/${form.get("analysis_id")}/resume`,{});revalidatePath("/review")}
