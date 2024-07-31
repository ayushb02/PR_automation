import github
import google.generativeai as genai
import requests
import time
import PyPDF2
import os
import smtplib


class PullNotifs:
    
    def __init__(self):
        self.git_client = github.Github("GITHUb ACCESS TOKEN")  
        self.pulls = []
        self.pull_counts = {}
        self.last_seen_pr = {}  
        genai.configure(api_key="GEMINI API KEY")
        self.model = genai.GenerativeModel('gemini-pro')
        self.guidelines = self.read_pdf('guidelines.pdf') 
        self.repo = self.git_client.get_user().get_repo("PR_automation")
        
    def read_pdf(self, file_path):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text

    def get_all_repos(self):
        self.pulls = []
        count = 0
        try:
            self.pulls.append(self.repo.get_pulls(state='open'))  
            self.pull_counts[count] = 0
            self.last_seen_pr[self.repo.name] = 0
            count += 1
        except github.GithubException as e:
            print(f"Error fetching repositories: {e}")

    def set_pull_counts(self):
        count = 0 
        for repo in self.pulls:
            for pr in repo:
                self.pull_counts[count] += 1
            count += 1
    
    def check_counts(self):
        counts_check = {}
        count = 0 
        try:
            pr_repos = self.repo.get_pulls(state='open') 
            counts_check[count] = 0
            for pr in pr_repos:
                counts_check[count] += 1
            count += 1
        except github.GithubException as e:
            print(f"Error checking PR counts: {e}")
        return self.pull_counts == counts_check
    
    def send_message(self):
        HOST = "smtp-mail.outlook.com"
        PORT = 587

        FROM_EMAIL = "OUTLOOK E-MAIl"
        TO_EMAIL = "RECIEVERS E-MAIl"
        PASSWORD = "OUTLOOK E-MAIL PASSWORD"

        MESSAGE = """Subject: New PR detected for review
        New PR detected in Repository "PR_automation" """

        smtp = smtplib.SMTP(HOST, PORT)

        status_code, response = smtp.ehlo()
        print(f"[*] Echoing the server: {status_code} {response}")

        status_code, response = smtp.starttls()
        print(f"[*] Starting TLS connection: {status_code} {response}")

        status_code, response = smtp.login(FROM_EMAIL, PASSWORD)
        print(f"[*] Logging in: {status_code} {response}")

        smtp.sendmail(FROM_EMAIL, TO_EMAIL, MESSAGE)
        smtp.quit()
       
    
    def read_files_from_pr(self, repo_name, pr_number):
        try:
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
        except github.GithubException as e:
            print(f"Error reading files from PR: {e}")
    
    def send_to_llm_for_review(self, file_content, pr):
        prompt = f"I am a software developer for a company and these is a code that i have written can you review it and suggest improvement also can you make sure the code followes the companies guidelines, here is the code   {file_content}\n\nHere are the companies Guidelines: {self.guidelines}"
        try:
            response = self.model.generate_content(prompt)
            self.send_message()
            print(response.text)
            pr.create_issue_comment(response.text)
        except Exception as e:
            print(f"Error sending content to LLM: {e}")
    
    def detect_new_prs_and_read_files(self):
        try:
            
            pr_repos = self.repo.get_pulls(state='open')
           
            for pr in pr_repos:
                if pr.number > self.last_seen_pr.get(self.repo.name, 0):
                    print(f"New PR detected in {self.repo.name}: PR #{pr.number} - {pr.title}")
                    self.read_files_from_pr(self.repo.full_name, pr.number)
                    self.last_seen_pr[self.repo.name] = pr.number
        except github.GithubException as e:
            print(f"Error detecting new PRs: {e}")

if __name__ == "__main__":
    labs = PullNotifs()
    labs.get_all_repos()
    labs.set_pull_counts()
    
    while True:
        if not labs.check_counts():
            labs.pull_counts = {}
            labs.get_all_repos()
            labs.set_pull_counts()
        labs.detect_new_prs_and_read_files()
        
        time.sleep(60)
