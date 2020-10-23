# -*- coding: utf-8 -*-
from flask import json
from werkzeug.exceptions import HTTPException


class BaseError(HTTPException):
    message = '系统错误'
    status = 404
    status_code = 405001

    def __init__(self, message=None, status=None, status_code=None, header=None, *args, **kwargs):
        self.code = 200
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        if status:
            self.status = status
        super(BaseError, self).__init__(message, None)

    def get_body(self, environ=None):
        body = dict(
            status=self.status,
            message=self.message,
            status_code=self.status_code
        )
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None):
        return [('Content-Type', 'application/json')]

    @property
    def args(self):
        return self.message

class BaseErrorCode(HTTPException):
    message = '系统错误'
    code = 404
    success = False
    data = None

    def __init__(self, message=None, code=None, success=None, header=None, *args, **kwargs):
        self.code = 200
        if message:
            self.message = message
        if success:
            self.success = success
        if code:
            self.code = code
        super(BaseErrorCode, self).__init__(message, None)

    def get_body(self, environ=None):
        body = dict(
            code=self.code,
            message=self.message,
            success=self.success
        )
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None):
        return [('Content-Type', 'application/json')]

    @property
    def args(self):
        return self.message

class MethodNotAllowed(BaseErrorCode):
    code = 405
    success = False
    message = "方法不支持"


class SystemError(BaseErrorCode):
    code = 405
    message = '系统错误'
    success = False


class ApiError(BaseErrorCode):
    code = 405
    success = False
    message = "接口未注册"

class ParamsError(BaseErrorCode):
    code = 405
    success = False
    message = "参数缺失"

class NoPaper(BaseErrorCode):
    code = 405
    success = False
    message = "未找到该试卷"

class NoQuestion(BaseErrorCode):
    code = 405
    success = False
    message = "该试卷题目解析失败，请联系管理员..."

class ClassNoStudent(BaseErrorCode):
    code = 405
    success = False
    message = "该班级无学生"

class NoAnswer(BaseErrorCode):
    code = 405
    success = False
    message = "讲义生成中，请稍后..."

class NoErrCode(BaseErrorCode):
    code = 405
    success = False
    message = "该错误率以上无题目，请重新选择..."

class NotFound(BaseErrorCode):
    code = 405
    success = False
    message = "未找到该内容"

class UnknownQuestionType(BaseErrorCode):
    code = 405
    success = False
    message = "未知的题目类型，请联系管理员"