def year(request):
    from datetime import date
    return {
        'year': date.today().year,
    }
