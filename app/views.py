from django.shortcuts import render
from django.http import HttpResponse
from django import forms
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer

import requests
from urllib.parse import urlencode

from main.settings import STATICFILES_DIRS
from main.secret import SEARCH_ENGINE, TOKEN
from .constant import CR_CHOICES, GL_CHOICES, LR_CHOICES
# Create your views here.

URL = 'https://customsearch.googleapis.com/customsearch/v1'

cr_choices = CR_CHOICES
gl_choices = GL_CHOICES
lr_choices = LR_CHOICES

def get_data(URL, params):
    r = requests.get(URL, params=params)
    data = r.json()
    return data

class SearchForm(forms.Form):
    search_string = forms.CharField(label='Введите запрос:', max_length=100)
    country_restrict = forms.ChoiceField(label='Страна поиска:', choices=cr_choices)
    geolocation = forms.ChoiceField(label='Местоположение:', choices=gl_choices)
    language_restrict = forms.ChoiceField(label='Язык поиска:', choices=lr_choices)

class GetIndex(APIView):
    
    renderer_classes = [TemplateHTMLRenderer]
    form = SearchForm()
    
    current_page = 1
    base_url = ''
    
    context = {
        'form': form,
        'dirs': STATICFILES_DIRS,
        }
    
    params = {
        'cx': SEARCH_ENGINE,
        'key': TOKEN,
        'start': current_page,
    }
    
    def get(self, request):
        self.updateContext(request) 
        return Response(self.context, template_name='index.html')
    
    def post(self, request):     
        search_string = request.POST.get('search_string')
        country_restrict = request.POST.get('country_restrict')
        geolocation = request.POST.get('geolocation')
        language_restrict = request.POST.get('language_restrict')
        
        self.params.update({'q': search_string})
        
        if not country_restrict == 'all':
            self.params.update({'cr': country_restrict})
            
        if not geolocation == 'all':
            self.params.update({'gl': geolocation})
            
        if not language_restrict == 'all':
            self.params.update({'lr': language_restrict})
            
        self.updateContext(request)
        
        return Response(self.context, template_name='index.html')
    
    
    def updateContext(self, request):
        current_page = int(request.GET.get('page', 0))
        print(current_page, self.current_page)
        if not current_page == self.current_page:
            print('not')
            self.current_page = current_page
        else:
            print('yes')
            self.current_page = 1
        
        self.params['start'] = self.current_page
        data = get_data(URL, params=self.params)
        
        items = data.get('items')
        total_result = data.get('searchInformation', {}).get('totalResults', 0)
        next_index = data.get('queries', {}).get('nextPage', [{}])[0].get('startIndex')
        prev_index = data.get('queries', {}).get('previousPage', [{}])[0].get('startIndex')
        
        if next_index:
            next_page_url = self.base_url + '?' + urlencode({'page': next_index})
            curr_page = (next_index - 10) % 10
            self.context.update({'next_page_url': next_page_url})
        else:
            self.context.update({'next_page_url': 0})
            
        if prev_index:
            prev_page_url = self.base_url + '?' + urlencode({'page': prev_index})
            self.context.update({'prev_page_url': prev_page_url})
        else:
            self.context.update({'prev_page_url': 0})

        self.context.update({
        'items': items,
        'total_result': total_result,
        })
