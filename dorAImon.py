import tkinter as tk
from tkinter import scrolledtext, messagebox, Canvas, Frame
import requests
from bs4 import BeautifulSoup
import textwrap
import google.generativeai as genai
from flask import Flask, request, render_template


def to_markdown(text):
    text = text.replace('•', '  *')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

# Function to scrape the website and its subpages
def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract main content
        content = soup.get_text()
        links = [a['href'] for a in soup.find_all('a', href=True) if url in a['href']]

        subpage_contents = []
        for link in links:
            try:
                sub_response = requests.get(link)
                sub_response.raise_for_status()
                sub_soup = BeautifulSoup(sub_response.text, 'html.parser')
                subpage_contents.append(sub_soup.get_text())
            except requests.RequestException as e:
                print(f"Error fetching subpage {link}: {e}")

        return content, subpage_contents
    except requests.RequestException as e:
        print(f"Error fetching main page: {e}")
        return "", []

# Function to preprocess the content
def preprocess_content(content_list):
    processed_content = []
    for content in content_list:
        #preprocessing
        processed_content.append(content.replace('\n', ' ').strip())
    return processed_content

# Function to generate answers using GEMINI API with context
def generate_answer(question, content):
    GOOGLE_API_KEY = "{YOUR_KEY!!}"
    genai.configure(api_key=GOOGLE_API_KEY)

    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

    # Provide the question and scraped content as context
    context = "Context: " + "\n\n".join(content)
    combined_text = question + "\n" + context
    response = model.generate_content(combined_text)
    return response.text

# Function to handle the button click
def on_ask_question():
    url = url_entry.get()
    question = question_entry.get()
    
    main_content, subpage_contents = scrape_website(url)
    content_to_process = [main_content] + subpage_contents
    processed_content = preprocess_content(content_to_process)
    
    answer = generate_answer(question, processed_content)
    add_message("You", question)
    add_message("dorAImon", answer)

# Function to add messages to the chat history
def add_message(sender, message):
    
    frame = Frame(chat_display_frame, bg="lightgrey", bd=2, relief="solid")
    frame.pack(padx=5, pady=5, fill="x", expand=True)
    
    sender_label = tk.Label(frame, text=f"{sender}:", font=('Helvetica', 10, 'bold'), bg="lightgrey")
    sender_label.pack(anchor="w")

    message_label = tk.Label(frame, text=message, font=('Helvetica', 10), wraplength=500, justify="left", bg="lightgrey")
    message_label.pack(anchor="w", padx=10, pady=5)
    
    # Scroll the canvas to the end
    chat_display_canvas.yview_moveto(1)

# Function to show the entire chat history
def show_chat_history():
    messagebox.showinfo("Chat History", chat_display_frame.get("1.0", tk.END))

# Interface design
# main window of the interface
root = tk.Tk()
root.title("dorAImon")
root.configure(bg="#2c3e50")

# for the url
tk.Label(root, text="Website URL:", bg="#2c3e50", fg="white", font=("Helvetica", 12, "bold")).pack(pady=(10, 5))
url_entry = tk.Entry(root, width=50, font=("Helvetica", 10))
url_entry.pack(pady=(0, 10))

# question entry
tk.Label(root, text="Question", bg="#2c3e50", fg="white", font=("Helvetica", 12, "bold")).pack(pady=(0, 5))
question_entry = tk.Entry(root, width=50, font=("Helvetica", 10))
question_entry.pack(pady=(0, 10))

# generation button
ask_button = tk.Button(root, text="Ask the Question", fg='white', font=('Helvetica', 10, 'bold'), bg='red', command=on_ask_question)
ask_button.pack(pady=(5, 10))

# chat display canvas
chat_display_canvas = Canvas(root, width=800, height=400, bg="white")
chat_display_canvas.pack(pady=(10, 10))

# scrollbar for the canvas
scrollbar = tk.Scrollbar(root, command=chat_display_canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chat_display_canvas.configure(yscrollcommand=scrollbar.set)

# frame inside the canvas
chat_display_frame = Frame(chat_display_canvas, bg="white")
chat_display_frame.bind(
    "<Configure>",
    lambda e: chat_display_canvas.configure(
        scrollregion=chat_display_canvas.bbox("all")
    )
)

chat_display_canvas.create_window((0, 0), window=chat_display_frame, anchor="nw")

# event looping
root.mainloop()