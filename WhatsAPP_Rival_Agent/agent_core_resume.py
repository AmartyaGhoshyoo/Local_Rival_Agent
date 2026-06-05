import json
import os
import subprocess
import tempfile
import asyncio
import shutil
from typing import Any
from agents import Agent, Runner, function_tool
from session import UserContext, get_user_context, get_agent_session
from resume_template import LATEX_TEMPLATE
from whatsapp_api import send_pdf_document, send_text_message

GLOBAL_SENDER_ID = None
# =========================================================
# 1. THE PLAIN PYTHON FUNCTION (Safe for Direct Local Testing)
# =========================================================
def raw_compile_and_send_resume(context: UserContext, resume_data_json: str) -> str:
    print("\n--- [DEBUG] STARTING COMPILATION ---")
    
    try:
        data = json.loads(resume_data_json)
    except json.JSONDecodeError as e:
        print(f"❌ JSON PARSE ERROR: {e}")
        return "Error: Invalid JSON formatting. The agent failed to escape characters."

    # Inject data
    tex_content = LATEX_TEMPLATE.replace("<<NAME>>", data.get("name", "Name Missing"))
    tex_content = tex_content.replace("<<ADDRESS>>", data.get("address", ""))
    tex_content = tex_content.replace("<<EMAIL>>", data.get("email", ""))
    tex_content = tex_content.replace("<<PHONE>>", data.get("phone", ""))
    tex_content = tex_content.replace("<<LINKEDIN>>", data.get("linkedin", ""))
    tex_content = tex_content.replace("<<GITHUB>>", data.get("github", ""))
    tex_content = tex_content.replace("<<SUMMARY>>", data.get("summary", ""))
    tex_content = tex_content.replace("<<EDUCATION_TEX>>", data.get("education_tex", ""))
    tex_content = tex_content.replace("<<EXPERIENCE_TEX>>", data.get("experience_tex", ""))
    tex_content = tex_content.replace("<<PROJECTS_TEX>>", data.get("projects_tex", ""))
    tex_content = tex_content.replace("<<SKILLS_TEX>>", data.get("skills_tex", ""))

    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, "resume.tex")
        pdf_path = os.path.join(temp_dir, "resume.pdf")
        log_path = os.path.join(temp_dir, "resume.log")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        print("-> Saved resume.tex. Running Tectonic...")
        
        # Run Tectonic
        compile_process = subprocess.run(
            ["tectonic", "--print", "--outdir", temp_dir, tex_path], 
            capture_output=True, 
            text=True
        )

        # IF PDF WAS NOT GENERATED, READ THE .LOG FILE!
        if not os.path.exists(pdf_path):
            print("\n❌ TECTONIC COMPILATION FAILED!")
            
            if os.path.exists(log_path):
                print("=== RESUME.LOG (THE TRUTH) ===")
                with open(log_path, "r", encoding="utf-8") as log_file:
                    print(log_file.read())
                print("==============================")
            else:
                print("No log file was generated. Tectonic crashed completely.")
                print(f"STDOUT: {compile_process.stdout}")
                print(f"STDERR: {compile_process.stderr}")

            return "Error: LaTeX Compilation failed."

        print("✅ PDF generated successfully!")
        
        try:
            # Use the global variable here instead of context!
            send_pdf_document(GLOBAL_SENDER_ID, pdf_path)
        except Exception as e:
            print(f"⚠️ WhatsApp Upload skipped or failed: {e}")

    return "Success: PDF compiled and sent."


# =========================================================
# 2. THE REGISTERED AGENT TOOL (Wrapped for LLM use)
# =========================================================
@function_tool
def compile_and_send_resume(context: UserContext, resume_data_json: str) -> str:
    """
    Call this ONLY when you have collected ALL information from the user.
    resume_data_json must contain keys: name, address, email, phone, linkedin, github, 
    summary, education_tex, experience_tex, projects_tex, skills_tex.
    """
    try:
        send_text_message(context.session_id, "⚙️ I have all your details! Compiling your professional LaTeX resume now...")
    except Exception:
        pass # Ignore API error if testing locally in terminal
    
    return raw_compile_and_send_resume(context, resume_data_json)

# =========================
# AGENT SETUP
# =========================
def _build_system_prompt() -> str:
    return """You are an expert Resume Builder AI operating on WhatsApp. 
Your ONLY goal is to interview the user step-by-step to gather details, and then SILENTLY call the `compile_and_send_resume` tool. 
NEVER output raw LaTeX code directly to the user in chat.

**Interview Protocol:**
1. Greet the user. Ask if they want to build a resume.
2. Ask for details ONE OR TWO AT A TIME. Wait for their response. Do not overwhelm them.
   - Name, Address, Phone, Email
   - LinkedIn & GitHub URLs
   - Professional Summary
   - Education (Degree, University, Dates, CGPA)
   - Experience (Job Title, Company, Dates, and 2-3 bullet points)
   - Projects (Name, Link, 2 bullet points)
   - Skills (Languages, Frameworks, Tools)

**CRITICAL RULE FOR CALLING THE TOOL:**
When you have all the information, you MUST call the `compile_and_send_resume` tool. 
Because the payload is JSON, you MUST double-escape every single LaTeX backslash so the JSON remains valid.
Example: use \\\\textbf instead of \\textbf. Use \\\\begin instead of \\begin.

For `education_tex`:
\\\\begin{twocolentry}{\\\\textbf{Date - Date}}
    \\\\textbf{Degree} | University | CGPA
\\\\end{twocolentry}

For `experience_tex`:
\\\\begin{twocolentry}{\\\\textbf{Date - Date}}
    \\\\textbf{Job Title} | \\\\href{link}{\\\\textcolor{blue}{Company}} | Location
\\\\end{twocolentry}
\\\\vspace{0.02 cm}
\\\\begin{onecolentry}
    \\\\begin{highlights}
        \\\\item Bullet point 1
        \\\\item Bullet point 2
    \\\\end{highlights}
\\\\end{onecolentry}

For `projects_tex`:
\\\\begin{onecolentry}
    \\\\textbf{Project Name} | \\\\href{link}{\\\\textcolor{blue}{Live}}
    \\\\begin{highlights}
        \\\\item Detail 1
    \\\\end{highlights}
\\\\end{onecolentry}

For `skills_tex`:
\\\\textbf{Languages:} Python, C | \\\\textbf{Frameworks:} FastAPI...

After calling the tool, simply tell the user: "Your resume is compiling and will be sent shortly!"
"""

agent = Agent(
    name="Resume Builder Agent",
    instructions=_build_system_prompt(),
    model='gpt-4o', # Switched to gpt-4o for better strict tool calling
    tools=[compile_and_send_resume],
)

# =========================
# ASYNC EXECUTION RUNNER
# =========================
# =========================
# ASYNC EXECUTION RUNNER
# =========================
async def handle_user_message(user_text: str, sender_id: str) -> str:
    global GLOBAL_SENDER_ID
    GLOBAL_SENDER_ID = sender_id  # Set the global variable for the tool to grab
    
    context = get_user_context(sender_id)
    session = get_agent_session(sender_id)
    
    result = await Runner.run(agent, user_text, context=context, session=session)
    return result.final_output


if __name__ == "__main__":
    async def test_agent_tool_calling():
        test_sender_id = "agent_debug_user_777"
        
        # Pure Python file system wipe to avoid SDK method limitations
        db_dir = "User_Sessions_Directory"
        if os.path.exists(db_dir):
            try:
                shutil.rmtree(db_dir)
                print("🧼 Wiped previous session database folder on disk for a clean execution window...")
            except Exception as e:
                print(f"⚠️ Could not clear session directory automatically: {e}")
        
        print("\n================================================================")
        print("🤖 RESUME AGENT - WORKFLOW & TOOL CALLING TEST HARNESS")
        print("================================================================")
        print("Options:")
        print("1. Chat normally to step through the collection interview manually.")
        print("2. Type 'trigger tool' to smash the agent with a complete profile")
        print("   all at once, forcing it to call 'compile_and_send_resume'.")
        print("3. Type 'exit' to quit.")
        print("----------------------------------------------------------------\n")

        while True:
            try:
                user_input = input("👤 You: ").strip()
                if user_input.lower() == "exit":
                    print("👋 Exiting agent test runner.")
                    break
                
                # SHORTCUT: Forces all data into the context window to evaluate the model's tool selection
                if user_input.lower() == "trigger tool":
                    user_input = (
                        "I am providing all my profile data completely right now. "
                        "Do not ask me any further questions. Immediately call your "
                        "compile_and_send_resume tool with this information converted to JSON:\n\n"
                        "Name: Amartya Ghosh\n"
                        "Address: Shillong, Meghalaya 793006\n"
                        "Email: amartyaghosh40@gmail.com\n"
                        "Phone: +91 7093854769\n"
                        "LinkedIn: https://www.linkedin.com/in/amartya-ghosh-2b9b7b22b/\n"
                        "GitHub: https://github.com/AmartyaGhoshyoo\n"
                        "Summary: AI/ML Engineer with 1 year+ internship experience building production AI systems.\n"
                        "Education: B.Tech in Computer Science and Engineering, NIT Meghalaya, Nov 2022 - May 2026, CGPA: 8.71/10.00\n"
                        "Experience: Software Development Engineer - AI at Rival.io, Dec 2025 - Present. Engineered an AI-driven WhatsApp developer assistant.\n"
                        "Projects: Agentic WebPilot. Autonomous web navigation backend using OpenAI SDK agent architecture.\n"
                        "Skills: Languages: Python, C, SQL. Frameworks: FastAPI, Redis, PostgreSQL.\n"
                    )
                    print("\n🚀 Injecting full profile block into the LLM context window...")

                if not user_input:
                    continue

                print("Thinking/Executing Tools...")
                response = await handle_user_message(user_input, test_sender_id)
                print(f"🤖 Agent Response:\n{response}\n")

            except KeyboardInterrupt:
                print("\n👋 Execution interrupted.")
                break
            except Exception as e:
                print(f"🚨 Framework Error: {e}\n")

    # Run the test loop
    asyncio.run(test_agent_tool_calling())