from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'abouts/author.html'


class AboutTechView(TemplateView):
    template_name = 'abouts/tech.html'
