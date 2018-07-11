from django.conf.urls import url, include
from apps.users import views

urlpatterns = [
    # 视图函数
    # url(r'^register$', views.register, name='register'),
    # url(r'^do_register$', views.do_register, name='do_register'),

    # 类视图来进行改善（代替前面的视图函数), as_view返回一个视图函数，后面的括号不能漏
    url(r'^register$', views.RegisterView.as_view(), name='register'),
    url(r'^login$', views.LoginView.as_view(), name='login'),
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),
    url(r'^active/(.+)$', views.ActiveView.as_view(), name='register'),
]
