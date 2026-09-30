"""
app.py — Gradio Web Interface for the University PDF RAG Chatbot
=================================================================
Run:  python app.py
Then open the URL shown in the terminal (usually http://127.0.0.1:7860)
"""

import gradio as gr
from rag import ask_question

# ─── Chat Handler ────────────────────────────────────────────────────────────────

def respond(message: str, chat_history: list) -> tuple:
    """
    Called every time the user sends a message.
    Runs the RAG pipeline and appends the result to the chat history.
    """
    if not message.strip():
        return "", chat_history

    try:
        result = ask_question(message)
        answer = result["answer"]
        sources = result["sources"]

        # Combine answer + sources into one bot message
        bot_reply = f"{answer}\n\n---\n{sources}"

    except Exception as e:
        bot_reply = f"⚠️ An error occurred: {str(e)}"

    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": bot_reply})
    return "", chat_history


def clear_chat():
    """Clears the chat history."""
    return [], ""


# ─── Gradio UI ───────────────────────────────────────────────────────────────────

with gr.Blocks(
    title="University PDF RAG Chatbot"
) as demo:

    # Header
    gr.Markdown(
        """
        # 🎓 University PDF RAG Chatbot
        Ask any question about the university document.  
        The chatbot answers **only** from the uploaded PDF — no made-up information.
        """
    )

    # Chatbot area
    chatbot = gr.Chatbot(
        label="Chat",
        height=450,
        elem_id="chatbot-area"
    )

    # Input row
    with gr.Row():
        msg_input = gr.Textbox(
            placeholder="Type your question here … e.g. What is the attendance requirement?",
            show_label=False,
            scale=5,
            elem_id="user-input"
        )
        ask_btn = gr.Button("🔍 Ask", variant="primary", scale=1, elem_id="ask-button")

    # Clear button
    clear_btn = gr.Button("🗑️ Clear Chat", elem_id="clear-button")

    # Footer info
    gr.Markdown(
        """
        ---
        **How it works:**  
        Your question → Embedding → Qdrant similarity search → Top 5 chunks retrieved →  
        Qwen LLM generates an answer grounded in the PDF content.
        """
    )

    # ── Event bindings ──────────────────────────────────────────────────────────

    # Ask button click
    ask_btn.click(
        fn=respond,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    )

    # Enter key submit
    msg_input.submit(
        fn=respond,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    )

    # Clear button
    clear_btn.click(
        fn=clear_chat,
        outputs=[chatbot, msg_input]
    )


# ─── Launch ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Starting University PDF RAG Chatbot ...")
    print("   Open the URL below in your browser.\n")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
        ),
        css="""
            .gradio-container { max-width: 850px !important; margin: auto; }
            footer { display: none !important; }
        """
    )
