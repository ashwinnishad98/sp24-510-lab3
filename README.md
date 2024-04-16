# Lab 3
## Data Storage with Python

A simple application to store all your ChatGPT prompts. 
Functionality
- Create new prompts
- Search functionality
- Sort by oldest or newest prompts
- Sort to view only favorite prompts (indicated by a star ★ next to the prompt title)
- Edit prompts
- Delete prompts 


### How to Run
Open your terminal (if in VS Code, press ```ctrl + ` ```).

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### What's Included
- app.py: The source code of the prompt application.
- env: A file to manage environment variables.

### Lessons Learned
- Using supabase to communicate with a Postgres database
- Rendering the UI based on database updates
