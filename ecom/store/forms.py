from django import forms

from store.models import ReviewRating


class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject',  'review', 'rating', ]
    # name = forms.CharField(max_length=100)
    # email = forms.EmailField()
    # subject = forms.CharField(max_length=100)
    # review = forms.CharField(widget=forms.Textarea)