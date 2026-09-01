---
name: pr-feedback
description: Process GitHub PR review comments through three checkpointed steps - fetch and analyze the feedback, fix and commit, then push. Use when the user wants to address reviewer comments on a GitHub PR, work through pending PR feedback, or respond to a code review left on GitHub.
---

Three-step workflow for acting on GitHub PR review comments, run with the `gh` CLI. Each step ends at a **checkpoint**: stop and get the user's explicit go-ahead before starting the next step. Never skip a checkpoint, even when a fix looks obvious or the user seems in a hurry.

## 1. Fetch and analyze

Identify the PR: if the current branch has one open, use it (`gh pr view --json number,url,headRefName`); otherwise ask the user for the PR number or URL.

Fetch every piece of feedback, not just the most recent:

- Inline review comments: `gh api repos/{owner}/{repo}/pulls/{pr}/comments --paginate`
- Review summaries (approve / request changes / general remarks): `gh pr view <pr> --json reviews`
- Top-level PR comments: `gh pr view <pr> --comments`

For each distinct comment, call one of:

- **Needs a fix** — describe the concrete code change you'd make.
- **No action needed** — state why (already addressed by a later commit, out of scope, a misreading of the code, a style opinion not worth chasing, etc.).

Checkpoint: present the full comment list with your needs-fix/no-action call and proposed fix per item, then wait for the user to approve, adjust, or reject entries before touching any code. If there are no open comments to act on, report that and stop here.

## 2. Fix and commit

Apply only the fixes the user approved at the checkpoint above. Run the project's existing build/lint/test commands relevant to the changed files before committing (skip only if the project has none).

Commit the changes, referencing the addressed comment(s) in the message where it aids traceability.

Checkpoint: show the diff summary and the commit(s) created, then wait for the user's go-ahead before pushing.

## 3. Push and settle threads

Push the branch to the PR's remote (`git push`).

Then settle every comment from step 1's list, so each thread reflects what actually happened:

- **Fixed**: mark its review thread resolved. Resolving needs the thread's GraphQL node ID, not the REST comment ID, so look it up first:

  ```
  gh api graphql -f query='
    query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        pullRequest(number:$number) {
          reviewThreads(first:100) {
            nodes { id isResolved comments(first:1) { nodes { databaseId } } }
          }
        }
      }
    }' -f owner=<owner> -f repo=<repo> -F number=<pr>
  ```

  Match `databaseId` to the comment ID from step 1, then resolve its thread:

  ```
  gh api graphql -f query='mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ thread { isResolved } } }' -f id=<thread-node-id>
  ```

- **No action needed**: reply on the same thread explaining why, so the reviewer sees the reasoning instead of silence:

  ```
  gh api repos/{owner}/{repo}/pulls/{pr}/comments/{comment_id}/replies -f body="<reason>"
  ```

  Leave this thread unresolved; that call belongs to the reviewer once they've read the explanation.

Checkpoint: report the push result (branch, remote, commit SHAs), which threads you resolved, and which replies you posted explaining unaddressed comments, then confirm with the user that the PR is ready for re-review.
