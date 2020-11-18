import threading
from typing import Optional

import googleapiclient.discovery
from flask import json
from oauth2client.client import GoogleCredentials

from config import AUTH_KEY, INSTANCE_NAME, PROJECT, USER_ID, ZONE


def alexa(request):
    ret = _auth_alexa(request)
    if ret:
        return _build_response(ret)
    thread = threading.Thread(target=_execute, args=(["start"]))
    thread.start()
    return _build_response("LeaveItToMe")


def server(request):
    _auth(request)
    function = request.args.get("function", "")
    return _execute(function)


def _execute(function) -> str:
    if function == "start":
        compute = _init()
        ret = _start_instance(compute, PROJECT, ZONE, INSTANCE_NAME)
        if ret:
            return "started"
        return "alreadyStarted"
    elif function == "stop":
        compute = _init()
        ret = _stop_instance(compute, PROJECT, ZONE, INSTANCE_NAME)
        if ret:
            return "stopped"
        return "alreadyStopped!"
    return "NotSupportedFunction"


def _init():
    credentials = GoogleCredentials.get_application_default()
    return googleapiclient.discovery.build("compute", "v1", credentials=credentials)


def _auth(request):
    if request.headers.get("Auth-Key") != AUTH_KEY:
        raise Exception("NotAuthorized!")


def _auth_alexa(request) -> Optional[str]:
    request_json = request.get_json(silent=True)
    if request_json["context"]["System"]["user"]["userId"] not in USER_ID:
        print(request_json["context"]["System"]["user"]["userId"])
        return "NotAuthorized"
    return None


def _start_instance(compute, project: str, zone: str, name: str) -> bool:
    instance = (
        compute.instances().get(project=project, zone=zone, instance=name).execute()
    )
    if instance["status"] == "TERMINATED":
        compute.instances().start(project=project, zone=zone, instance=name).execute()
        return True
    else:
        return False


def __start_instance(compute, project: str, zone: str, name: str):
    compute.instances().start(project=project, zone=zone, instance=name).execute()


def _stop_instance(compute, project: str, zone: str, name: str) -> bool:
    instance = (
        compute.instances().get(project=project, zone=zone, instance=name).execute()
    )
    if instance["status"] == "RUNNING":
        compute.instances().stop(project=project, zone=zone, instance=name).execute()
        return True
    else:
        return False


def _build_response(message: str) -> str:
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": _translate(message),
            }
        },
    }
    return json.dumps(response)


dictionary: dict = {
    "started": "起動しました",
    "stopped": "停止しました",
    "alreadyStarted": "すでに起動しています",
    "alreadyStopped": "すでに停止しています",
    "NotSupportedFunction": "その操作はサポートしていません",
    "NotAuthorized": "権限がありません",
    "LeaveItToMe": "私にお任せください",
}


def _translate(message: str) -> str:
    return dictionary[message]
