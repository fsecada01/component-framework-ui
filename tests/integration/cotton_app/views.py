from django.shortcuts import render


def form_field_view(request):
    return render(
        request,
        "cotton_gallery/form_field.html",
        {
            "name": "email",
            "label": "Email",
            "value": "",
            "error": "",
            "type": "email",
            "required": "false",
        },
    )


def modal_view(request):
    return render(request, "cotton_gallery/modal.html", {"modal_id": "test-modal"})


def card_view(request):
    return render(request, "cotton_gallery/card.html", {})
