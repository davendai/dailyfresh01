from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import View


class IndexView(View):
    """类视图：处理注册"""

    def get(self, request):
        """处理GET请求，返回注册页面"""
        user = request.user
        return render(request, 'index.html')
