import github
git_client = github.Github("ayushb02", "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")
repo = git_client.get_repo("ayushb02/blood_bank", lazy=False)

pulls = repo.get_pulls(state='open', sort='created', base='master')
pull_number = []
for i in pulls:
    pull_number.append(i.number)




for n in pull_number:
    pr = repo.get_pull(n)
    commits = pr.get_commits()
    for commit in commits:
        files = commit.files
        for file in files:
            filename = file.filename
            contents = repo.get_contents(filename, ref=commit.sha).decoded_content
            print(contents)

