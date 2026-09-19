import json
import os
import re
from typing import Any

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

app = FastAPI(title="ApplyAI AI Service", version="1.0.0")


class ResumeRequest(BaseModel):
    resumeText: str = Field(min_length=20)


class ResumeProfile(BaseModel):
    name: str = ""
    skills: list[str] = []
    education: list[str] = []
    experience: list[str] = []
    projects: list[str] = []


class JobRequest(BaseModel):
    title: str
    description: str = Field(min_length=40)


class JobAnalysis(BaseModel):
    requiredSkills: list[str] = []
    niceToHaveSkills: list[str] = []
    responsibilities: list[str] = []


class MatchRequest(BaseModel):
    resumeProfile: ResumeProfile
    jobAnalysis: JobAnalysis
    projects: list[str] = []


class MatchResult(BaseModel):
    matchScore: int = Field(ge=0, le=100)
    matchedSkills: list[str] = []
    missingSkills: list[str] = []
    mostRelevantProject: str = ""


class GenerateRequest(BaseModel):
    profile: dict[str, Any]
    job: dict[str, Any]
    mostRelevantProject: str = ""


class ApplicationAnswer(BaseModel):
    question: str
    answer: str


class ApplicationPackage(BaseModel):
    coverLetter: str
    answers: list[ApplicationAnswer]


def client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")
    return OpenAI(api_key=key)


def structured_call(system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    try:
        response = client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"{prompt}\nReturn JSON matching this shape: {json.dumps(schema)}"},
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return parsed
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI request failed: {exc}") from exc


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/parse-resume", response_model=ResumeProfile)
def parse_resume(request: ResumeRequest) -> ResumeProfile:
    result = structured_call(
        "You extract factual resume information. Never invent a skill, employer, degree, project, or date. Use concise strings and empty arrays when information is absent.",
        request.resumeText,
        {
            "name": "string",
            "skills": ["string"],
            "education": ["string"],
            "experience": ["string"],
            "projects": ["string"],
        },
    )
    return ResumeProfile.model_validate(result)


@app.post("/parse-job", response_model=JobAnalysis)
def parse_job(request: JobRequest) -> JobAnalysis:
    result = structured_call(
        "You extract requirements from a job description. Separate must-have skills from nice-to-have skills and list concrete responsibilities. Do not add technologies that are not present.",
        f"Job title: {request.title}\n\nJob description:\n{request.description}",
        {
            "requiredSkills": ["string"],
            "niceToHaveSkills": ["string"],
            "responsibilities": ["string"],
        },
    )
    return JobAnalysis.model_validate(result)


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]+", "", value.lower())


@app.post("/match", response_model=MatchResult)
def match_resume(request: MatchRequest) -> MatchResult:
    resume_skills = {normalized(skill): skill for skill in request.resumeProfile.skills}
    required = request.jobAnalysis.requiredSkills
    nice_to_have = request.jobAnalysis.niceToHaveSkills
    matched = [skill for skill in required if normalized(skill) in resume_skills]
    optional_matched = [skill for skill in nice_to_have if normalized(skill) in resume_skills]
    missing = [skill for skill in required if normalized(skill) not in resume_skills]
    required_weight = 0.8
    optional_weight = 0.2
    score = round(
        (len(matched) / len(required) * required_weight * 100 if required else 60)
        + (len(optional_matched) / len(nice_to_have) * optional_weight * 100 if nice_to_have else 0)
    )
    score = max(0, min(100, score))

    project_text = " ".join(request.projects).lower()
    relevant_project = ""
    if project_text and request.jobAnalysis.responsibilities:
        keywords = [word for word in re.findall(r"[a-zA-Z]{4,}", " ".join(request.jobAnalysis.responsibilities).lower())]
        project_candidates = [(project, sum(1 for word in keywords if word in project.lower())) for project in request.projects]
        relevant_project = max(project_candidates, key=lambda item: item[1])[0] if project_candidates else ""

    refinement = structured_call(
        "You are a careful reviewer. Refine only the relevant project choice from the provided project list. Do not change the numeric score or skill overlap.",
        json.dumps(
            {
                "projects": request.projects,
                "responsibilities": request.jobAnalysis.responsibilities,
                "matchedSkills": matched + optional_matched,
                "missingSkills": missing,
                "ruleBasedScore": score,
            }
        ),
        {"mostRelevantProject": "string"},
    )
    refined_project = refinement.get("mostRelevantProject", relevant_project)
    if refined_project not in request.projects:
        refined_project = relevant_project

    return MatchResult(
        matchScore=score,
        matchedSkills=matched + optional_matched,
        missingSkills=missing,
        mostRelevantProject=refined_project,
    )


@app.post("/generate", response_model=ApplicationPackage)
def generate(request: GenerateRequest) -> ApplicationPackage:
    result = structured_call(
        "You write honest, specific application materials from the supplied candidate profile and job. Never invent achievements, metrics, employers, or technologies. The cover letter must be 150-200 words. Return exactly 2 or 3 application answers.",
        json.dumps(
            {
                "profile": request.profile,
                "job": request.job,
                "mostRelevantProject": request.mostRelevantProject,
            }
        ),
        {
            "coverLetter": "150-200 word string",
            "answers": [{"question": "string", "answer": "string"}],
        },
    )
    package = ApplicationPackage.model_validate(result)
    if not 150 <= len(package.coverLetter.split()) <= 220:
        raise HTTPException(status_code=502, detail="Generated cover letter was outside the requested length")
    if len(package.answers) not in (2, 3):
        raise HTTPException(status_code=502, detail="Generated answer count was outside the requested range")
    return package


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AI_SERVICE_PORT", "8000")))