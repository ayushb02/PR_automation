import github
import google.generativeai as genai
import requests
import time
import PyPDF2
import os
from dotenv import load_dotenv, dotenv_values 

class PullNotifs:
    
    def __init__(self):
        self.git_client = github.Github(os.getenv('ACCESS_TOKEN'))  
        self.pulls = []
        self.pull_counts = {}
        self.last_seen_pr = {}  
        self.GOOGLE_API_KEY = os.getenv('API_KEY')
        genai.configure(api_key=self.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.guidelines = self.read_pdf('guidelines.pdf') 
        
    def read_pdf(self, file_path):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    def get_all_repos(self):
        self.pulls = []
        count = 0
        for repo in self.git_client.get_user().get_repos():
            self.pulls.append(repo.get_pulls(state='open'))  
            self.pull_counts[count] = 0
            self.last_seen_pr[repo.name] = 0
            count += 1
            
    def set_pull_counts(self):
        count = 0 
        for repo in self.pulls:
            for pr in repo:
                self.pull_counts[count] += 1
            count += 1
    
    def check_counts(self):
        counts_check = {}
        count = 0 
        for repo in self.git_client.get_user().get_repos():
            pr_repos = repo.get_pulls(state='open') 
            counts_check[count] = 0
            for pr in pr_repos:
                counts_check[count] += 1
            count += 1
        return self.pull_counts == counts_check
    
    def send_message(self):
        print("You have new pull requests!")
    
    def read_files_from_pr(self, repo_name, pr_number):
        repo = self.git_client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        files = pr.get_files()
        
        for file in files:
            file_content_url = file.raw_url
            response = requests.get(file_content_url)
            if response.status_code == 200:
                file_content = response.text
                print(f"File Content for {file.filename}:")
                print(file_content)
                self.send_to_llm_for_review(file_content, pr)
            else:
                print(f"Error fetching file content for {file.filename}: {response.status_code}")
    
    def send_to_llm_for_review(self, file_content, pr):
        prompt = f"Review this code and comment about it: {file_content}\n\nGuidelines: {self.guidelines}"
        response = self.model.generate_content(prompt)
        print(response.text)
        pr.create_issue_comment(response.text)
    
    def detect_new_prs_and_read_files(self):
        for repo in self.git_client.get_user().get_repos():
            pr_repos = repo.get_pulls(state='open') 
            for pr in pr_repos:
                if pr.number > self.last_seen_pr.get(repo.name, 0):
                    print(f"New PR detected in {repo.name}: PR #{pr.number} - {pr.title}")
                    self.read_files_from_pr(repo.full_name, pr.number)
                    self.last_seen_pr[repo.name] = pr.number

if __name__ == "__main__":
    labs = PullNotifs()
    labs.get_all_repos()
    labs.set_pull_counts()
    
    while True:
        if not labs.check_counts():
            labs.send_message()
            labs.pull_counts = {}
            labs.get_all_repos()
            labs.set_pull_counts()
        labs.detect_new_prs_and_read_files()
        
        time.sleep(60)
