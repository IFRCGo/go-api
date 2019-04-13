from django.shortcuts import render

#x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#
#if x_forwarded_for:
#    ipaddress = x_forwarded_for.split(',')[-1].strip()
#else:
#    ipaddress = request.META.get('REMOTE_ADDR')
#get_ip= ip() #imported class from model
#get_ip.ip_address= ipaddress
#get_ip.pub_date = datetime.date.today() #import datetime
#get_ip.save()
#
#
##get_user_data= request.META.get('HTTP_USER_AGENT')
##get_ip.user_data= get_user_data
##get_ip.save()
