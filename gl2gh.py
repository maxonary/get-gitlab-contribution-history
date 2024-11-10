import subprocess
import os
import sys
from dotenv import load_dotenv

def transfer_commit_history(gitlab_repo, github_repo):
    SKIP_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".mov"]

    # Load the author email from the .env file
    load_dotenv()
    author_email = os.getenv("AUTHOR_EMAIL")

    if not author_email:
        print("Error: AUTHOR_EMAIL not found in .env file.")
        return

    try:
        # Clone the GitLab repository
        subprocess.run(['git', 'clone', gitlab_repo, 'gitlab_repo'])
        os.chdir('gitlab_repo')

        # Filter commits based on the specified author email
        for ext in SKIP_EXTENSIONS:
            subprocess.run(['git', 'filter-branch', '--force', '--index-filter',
                            f'git rm --cached --ignore-unmatch *{ext}',
                            '--prune-empty', '--tag-name-filter', 'cat',
                            '--msg-filter', f"grep '{author_email}' || echo SKIP", '--', '--all'])

        # Filter commits by author email
        subprocess.run(['git', 'filter-branch', '--force', '--commit-filter',
                        f'if [ "$GIT_COMMITTER_EMAIL" = "{author_email}" ]; then git commit-tree "$@"; else skip_commit "$@"; fi', '--all'])

        # Add GitHub repository as remote and push the filtered commits
        subprocess.run(['git', 'remote', 'add', 'github', github_repo])
        subprocess.run(['git', 'fetch', 'github'])
        subprocess.run(['git', 'checkout', '-b', 'new_branch'])
        subprocess.run(['git', 'push', 'github', 'new_branch'])

        # Merge and handle conflicts
        merge_process = subprocess.Popen(['git', 'merge', 'github/new_branch', '--allow-unrelated-histories'],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        merge_output, merge_error = merge_process.communicate()

        if merge_process.returncode != 0:
            if b'CONFLICT' in merge_error:
                print("Merge conflict detected. Please resolve conflicts manually and then run the script again.")
            else:
                print("An error occurred while merging branches:", merge_error.decode())
            return

        # Final push to GitHub master branch
        subprocess.run(['git', 'push', 'github', 'master'])

        print("Commit history successfully transferred from GitLab to GitHub for specified author.")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <gitlab_repo_url> <github_repo_url>")
        sys.exit(1)

    gitlab_repo_url = sys.argv[1]
    github_repo_url = sys.argv[2]

    transfer_commit_history(gitlab_repo_url, github_repo_url)