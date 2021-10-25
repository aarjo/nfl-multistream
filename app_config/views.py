from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from services import nfldataservice

def index(request):
    context = {'nfldata': nfldataservice.getJsonData()}
    return render(request, 'home.html', context)

def nfldata(request):
    return JsonResponse(nfldataservice.getJsonData())
