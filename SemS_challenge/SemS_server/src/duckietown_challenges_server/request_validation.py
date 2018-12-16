# coding=utf-8
from pyramid.httpexceptions import HTTPBadRequest


def challenge_ids_list_validator(challenge_id):
    if not challenge_id:
        return True
    # split and validate
    parts = challenge_id.split(',')
    for p in parts:
        if len(p) > 0 and not p.isdigit():
            raise HTTPBadRequest('The parameter `challenge_id` must be a comma-separated sequence of integers')
    # return success
    return True
