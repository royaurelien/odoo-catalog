# -*- coding: utf-8 -*-
#!/bin/python3


def prepare_commit(item):
    commit = item.commit
    committer = commit.committer

    return {
        "name": commit.message,
        "author": committer.name,
        "email": committer.email,
        "commit_id": item.sha,
        "commit_url": item.html_url,
        "commit_date": committer.date,
    }
