import github

class PullNotifs:
    
    def __init__(self):
        self.git_client = github.Github("ayushb02", "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")
        self.pulls = []
        self.pull_counts = {}
        self.repo = []
        
    def get_all_repos(self):
        self.pulls = []
        count = 0
        for i in self.git_client.get_user().get_repos():
            self.pulls.append(i.get_pulls('all'))
            self.repo.append(i)
            self.pull_counts[count] = 0
            count += 1
            
    def set_pull_counts(self):
        count = 0 
        for repo in self.pulls:
            for j in repo:
                self.pull_counts[count] = self.pull_counts[count] + 1
            count += 1
    
    def check_counts(self):
        counts_check = {}
        count = 0 
        for pl in self.git_client.get_user().get_repos():
            pl_repos = pl.get_pulls('all')
            counts_check[count] = 0
            for repo in pl_repos:
                counts_check[count] = counts_check[count] + 1
            count += 1
        return self.pull_counts == counts_check
    
    def send_message(self):
       print("PR detected")
       for rep in self.repo:
         for pr in self.pulls:
             p =  self.repo.get_pull(pr.number)
             commits = p.get_commits()
             for commit in commits:
                 files = commit.files
                 for file in files:
                   filename = file.filename
                   contents = rep.get_contents(filename, ref=commit.sha).decoded_content
                   print(contents)



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