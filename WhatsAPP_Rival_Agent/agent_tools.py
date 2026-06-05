import json
import os
import subprocess
import tempfile
from resume_template import LATEX_TEMPLATE
from whatsapp_api import send_pdf_document, send_text_message

# Give this instruction to your LLM agent so it knows how to behave
AGENT_SYSTEM_PROMPT = """
You are a friendly, professional Resume Builder Assistant operating on WhatsApp. 
Your goal is to interview the user to collect data for a LaTeX resume.

Follow these steps exactly:
1. Greet the user and ask if they are ready to build their resume.
2. Ask for the following information ONE BY ONE (wait for their answer before moving to the next):
   - Full Name
   - Email and Phone Number
   - A brief summary (1-2 sentences)
   - Top 5 Skills (comma separated)
   - Most recent job title and company
3. Once you have ALL the information, compile it into a JSON string.
4. Call the `compile_and_send_resume` tool with that JSON data.
5. Tell the user their resume is compiling and will arrive in a few seconds.

Keep your tone conversational. Use standard WhatsApp formatting (*bold*, _italics_).
"""

# Register this as a tool in your LLM runner
def compile_and_send_resume(sender_id: str, resume_json_string: str) -> str:
    """
    Called by the LLM when all resume data is collected. 
    Expects a JSON string with keys: name, contact, summary, skills, experience.
    """
    send_text_message(sender_id, "⚙️ Generating your PDF... Please hold on a moment.")
    
    try:
        data = json.loads(resume_json_string)
    except json.JSONDecodeError:
        return "Error: The AI provided invalid JSON data."

    # 1. Inject user data into the LaTeX template
    tex_content = LATEX_TEMPLATE.replace("{{NAME}}", data.get("name", "Name Missing"))
    tex_content = tex_content.replace("{{CONTACT}}", data.get("contact", ""))
    tex_content = tex_content.replace("{{SUMMARY}}", data.get("summary", ""))
    tex_content = tex_content.replace("{{SKILLS}}", data.get("skills", ""))
    tex_content = tex_content.replace("{{EXPERIENCE}}", data.get("experience", ""))

    # 2. Setup a temporary directory for safe compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, "resume.tex")
        pdf_path = os.path.join(temp_dir, "resume.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        
# 3. Run the local LaTeX compiler
        try:
            compile_process = subprocess.run(
                ["tectonic", "--outdir", temp_dir, tex_path],
                capture_output=True,
                text=True,
                timeout=15
            )
        except FileNotFoundError:
            return "Error: 'pdflatex' compiler is not installed on the server."

        if not os.path.exists(pdf_path):
            print("LaTeX Error:", compile_process.stdout)
            return "Error: LaTeX Compilation failed."

        # 4. Send the compiled PDF via WhatsApp
        send_pdf_document(sender_id, pdf_path)

    return "Success: PDF compiled and sent."