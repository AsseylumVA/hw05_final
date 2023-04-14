def year(request):
    from datetime import datetime
    return {
        'year': datetime.utcnow().year,
    }
