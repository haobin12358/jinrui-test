# -*- coding: utf-8 -*-
from flask import json, request

from .error_response import BaseErrorCode, BaseError


class Success(BaseError):
    """
    成功信息, 不要被基类迷惑
    """
    status = 200
    message = '获取成功'
    data = None

    def __init__(self, message=None, data=None, *args, **kwargs):
        self.status_code = None
        if message is not None:
            self.message = message
        if data is not None:
            self.data = data
        super(Success, self).__init__(*args, **kwargs)

    def get_body(self, environ=None, *args, **kwargs):
        self.body = self._get_body()
        self.set_body(**kwargs)
        text = json.dumps(self.body)
        return text

    def set_body(self, **kwargs):
        self.body = self._get_body()
        self.body.update(kwargs)

    def _get_body(self):
        if hasattr(self, 'body'):
            return self.body
        body = dict(
            status=self.status,
            message=self.message,
        )
        if self.data is not None:
            body['data'] = self.data
        if hasattr(request, 'page_all'):
            body['total_page'] = request.page_all
        if hasattr(request, 'mount'):
            body['total_count'] = request.mount
        return body

class SuccessCode(BaseErrorCode):
    """
        成功信息, 不要被基类迷惑
        """
    code = 200
    message = '获取成功'
    data = None
    success = True

    def __init__(self, message=None, data=None, *args, **kwargs):
        if message is not None:
            self.message = message
        if data is not None:
            print(3)
            self.data = data
        super(SuccessCode, self).__init__(*args, **kwargs)

    def get_body(self, environ=None, *args, **kwargs):
        print(1)
        self.body = self._get_body()
        self.set_body(**kwargs)
        text = json.dumps(self.body)
        return text

    def set_body(self, **kwargs):
        print(2)
        self.body = self._get_body()
        self.body.update(kwargs)

    def _get_body(self):
        print(4)
        if hasattr(self, 'body'):
            return self.body
        body = dict(
            code=self.code,
            message=self.message,
            success=self.success
        )
        if self.data is not None:
            body['data'] = self.data
        if hasattr(request, 'page_all'):
            body['total_page'] = request.page_all
        if hasattr(request, 'mount'):
            body['total_count'] = request.mount
        return body
