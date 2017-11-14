from django.shortcuts import render

def hello(request):
    return render(request, 'writeinpublic/test.html')
