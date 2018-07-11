import re
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from django.db.utils import IntegrityError
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired
from apps.users.models import User
from dailyfresh01 import settings
from celery_tasks.tasks import send_active_mail


def register(request):
    return render(request, 'register.html')


def do_register(request):
    return HttpResponse('注册成功，进入登录界面')


class RegisterView(View):
    """类视图：处理注册"""

    def get(self, request):
        """处理GET请求，返回注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """处理POST请求，实现注册逻辑"""
        # 获取post请求参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # todo:校验参数合法性
        # 判断参数不能为空
        if not all([username, password, password2, email]):
            return render(request, 'register.html', {'errmsg': '参数不能为空'})

        # 判断2次输入的密码一致
        if password != password2:
            return render(request, 'register.html', {'errmsg': '两次输入的密码不一致'})

        # 判断邮箱合法性：
        if not re.match('^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱不合法'})

        # 判断是否勾选用户协议（勾选后得到：on）
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请勾选用户协议'})

        # 处理业务：保存用户到数据库表中
        # 这是django提供的方法，会对密码进行加密
        user = None
        try:
            user = User.objects.create_user(username, email, password)  # type:User
            # 修改用户状态为未激活
            user.is_active = False
            user.save()
        except IntegrityError:
            # 判断用户是否存在
            return render(request, 'register.html', {'errmsg': '用户已存在'})

        # todo:发送激活邮件
        token = user.generate_active_token()
        # 同步发送：会阻塞，不采取这种发送方式
        # RegisterView.send_active_mail(username, email, token)

        # 使用celery异步发送：不会阻塞(会保存方法名到Redis数据库中)
        send_active_mail.delay(username, email, token)

        return HttpResponse('注册成功，进入登录界面')

    @staticmethod
    def send_active_mail(username, email, token):
        """发送激活邮件"""
        subject = "天天生鲜激活邮件"  # 标题, 不能为空，否则报错
        message = ""  # 邮件正文(纯文本)
        sender = settings.EMAIL_FROM  # 发件人
        recipient_list = [email]  # 接收人, 需要是列表
        # 邮件正文(带html样式)
        html_message = ('<h3>尊敬的%s：感谢注册天天生鲜</h3>'
                        '请点击以下链接激活您的帐号:<br/>'
                        '<a href="http://127.0.0.1:8000/users/active/%s">'
                        'http://127.0.0.1:8000/users/active/%s</a>'
                        ) % (username, token, token)
        send_mail(subject, message, sender, recipient_list, html_message=html_message)


class ActiveView(View):
    def get(self, request, token: str):
        try:
            # 解密token:
            s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600*24)
            # 字符串转换为bytes类型
            dict_data = s.loads(token.encode())

        except SignatureExpired:
            return HttpResponse('激活链接已失效')

        # 获取用户id
        user_id = dict_data.get('confirm')

        # 修改字段已激活
        User.objects.filter(id=user_id).update(is_active=True)

        return HttpResponse('激活成功，跳转到登录界面')


class LoginView(View):
    def get(self, request):
        """处理GET请求，进入登录页面"""
        return render(request, 'login.html')

    def post(self, request):
        """处理GET请求，进入登录页面"""
        # 获取登录参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        # 校验参数合法性
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '用户名和密码不能为空'})

        # 通过 django 提供的authenticate方法：
        user = authenticate(username=username, password=password)
        # 判断用户名和密码是否正确
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名和密码不正确'})

        # 判断用户名是否激活
        if user.is_active:
            return render(request, 'login.html', {'errmsg': '用户名未激活'})

        # 通过django的login方法，保存登录用户状态（使用session）
        login(request, user)

        if remember == 'on':
            # 默认保持登录状态2周
            request.session.set_expiry(None)
        else:
            # 如果不设置有效期，关闭浏览器后登录状态失效
            request.session.set_expiry(0)
        return redirect(reversed('goods:index'))


class LogoutView(object):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))