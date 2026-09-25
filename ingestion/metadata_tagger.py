import json
import re

def extract_metadata(chunk_text: str, llm) -> dict:

    prompt = f"""
        You are a corporate policy document parser.
        Extract the following metadata from the text below.
        Return ONLY valid JSON, no explanation, no markdown.

        Fields to extract:
            - document_id: policy code if visible (e.g. TRV-POL-2005-V3), else null
            - policy_category: one of [Travel, HR, Finance, IT, Legal, Compliance, Other]
            - policy_owner: department name if mentioned, else null
            - effective_date: date in YYYY-MM-DD format if mentioned, else null

        Text:
        \"\"\"
        {chunk_text[:800]}
        \"\"\"

        JSON:
    """

    response = llm.invoke(prompt).content.strip()

    # Strip markdown code fences if the model wraps its output
    response = re.sub(r"```json|```", "", response).strip()

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "document_id": None,
            "policy_category": "Other",
            "policy_owner": None,
            "effective_date": None
        }
