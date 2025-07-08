import pytest
from django.urls import reverse

from apps.lexicon import models


@pytest.mark.django_db
class TestParadigmModal:
    def test_get_paradigm_modal(
        self, client, permissioned_user, english_project, english_words_with_paradigm
    ):
        """Test that the paradigm modal view renders correctly."""
        client.force_login(permissioned_user)
        words, paradigm, _ = english_words_with_paradigm
        url = reverse(
            "lexicon:paradigm_modal", args=[english_project.language_code, words[0].pk]
        )
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context
        assert "object" in response.context
        assert response.context["object"].pk == words[0].pk

    def test_post_paradigm_modal(
        self, client, permissioned_user, english_project, english_words_with_paradigm
    ):
        """Test that the paradigm modal view processes the form correctly."""
        client.force_login(permissioned_user)
        words, paradigm, _ = english_words_with_paradigm
        url = reverse(
            "lexicon:paradigm_modal", args=[english_project.language_code, words[1].pk]
        )
        data = {"paradigm": paradigm.pk}
        response = client.post(url, data, HTTP_HX_REQUEST="true")
        assert response.status_code == 204
        # Check that the paradigm was added to the word
        word = models.LexiconEntry.objects.get(pk=words[1].pk)
        assert paradigm in word.paradigms.all()
        # Check for HX-Trigger header
        assert response["HX-Trigger"] == "paradigmSaved"

    def test_get_paradigm_modal_forbidden(self, client, user, english_project, english_words_with_paradigm):
        """Unpermissioned user should not be able to GET the paradigm modal."""
        client.force_login(user)
        words, paradigm, _ = english_words_with_paradigm
        url = reverse(
            "lexicon:paradigm_modal", args=[english_project.language_code, words[0].pk]
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_post_paradigm_modal_forbidden(self, client, user, english_project, english_words_with_paradigm):
        """Unpermissioned user should not be able to POST the paradigm modal."""
        client.force_login(user)
        words, paradigm, _ = english_words_with_paradigm
        url = reverse(
            "lexicon:paradigm_modal", args=[english_project.language_code, words[1].pk]
        )
        data = {"paradigm": paradigm.pk}
        response = client.post(url, data, HTTP_HX_REQUEST="true")
        assert response.status_code == 403

    


@pytest.mark.django_db
class TestConjugationsView:
    def test_get_paradigm_view(self, client, permissioned_user, english_words_with_paradigm):
        """Test that the paradigm view renders correctly."""
        client.force_login(permissioned_user)
        words, paradigm, conjugation = english_words_with_paradigm
        url = reverse("lexicon:paradigm", args=[words[0].pk, paradigm.pk, "view"])
        response = client.get(url)
        assert response.status_code == 200
        assert "conjugation_grid" in response.context
        assert "forms_grid" in response.context
        assert response.context["word"].pk == words[0].pk
        assert response.context["paradigm"].pk == paradigm.pk

    def test_get_paradigm_edit(self, client, user, english_words_with_paradigm):
        """Test that the paradigm edit view renders correctly."""
        client.force_login(user)
        words, paradigm, conjugation = english_words_with_paradigm
        url = reverse("lexicon:paradigm", args=[words[0].pk, paradigm.pk, "edit"])
        response = client.get(url)
        assert response.status_code == 200
        assert "formset" in response.context
        assert "forms_grid" in response.context

    def test_post_paradigm_edit(self, client, permissioned_user, english_words_with_paradigm):
        """Test that the paradigm edit view updates a simple 1x1 conjugation"""
        client.force_login(permissioned_user)
        words, paradigm, conjugation = english_words_with_paradigm
        url = reverse("lexicon:paradigm", args=[words[0].pk, paradigm.pk, "edit"])
        # Get the formset to get the management form data
        response = client.get(url)
        formset = response.context["formset"]
        data = formset.management_form.initial
        # Update the conjugation value
        for i, form in enumerate(formset.forms):
            data[f"form-{i}-conjugation"] = f"updated_{i}"
            data[f"form-{i}-id"] = (
                form.instance.id if form.instance.id is not None else ""
            )

        data["form-TOTAL_FORMS"] = formset.total_form_count()
        data["form-INITIAL_FORMS"] = formset.initial_form_count()
        data["form-MIN_NUM_FORMS"] = 0
        data["form-MAX_NUM_FORMS"] = 1000
        post_response = client.post(url, data)
        assert post_response.status_code == 200
        # Check that the conjugation was updated in the database
        conjugations = models.Conjugation.objects.filter(
            word=words[0], paradigm=paradigm
        ).order_by("id")
        for i, conj in enumerate(conjugations):
            assert conj.conjugation == f"updated_{i}"

    def test_get_paradigm_edit_allowed(
        self, client, permissioned_user, english_words_with_paradigm
    ):
        """Unpermissioned user should be able to GET the paradigm edit view."""
        client.force_login(permissioned_user)
        words, paradigm, conjugation = english_words_with_paradigm
        url = reverse("lexicon:paradigm", args=[words[0].pk, paradigm.pk, "edit"])
        response = client.get(url)
        assert response.status_code == 200

    def test_post_paradigm_edit_forbidden(
        self, client, user, english_words_with_paradigm
    ):
        """Unpermissioned user should NOT be able to POST the paradigm edit view."""
        client.force_login(user)
        words, paradigm, conjugation = english_words_with_paradigm
        url = reverse("lexicon:paradigm", args=[words[0].pk, paradigm.pk, "edit"])
        # Try to post minimal formset data
        response = client.post(url, {})
        assert response.status_code == 403


@pytest.mark.django_db
class TestConjugationsEdit:
    def get_edit_url(self, word, paradigm):
        return reverse("lexicon:paradigm", args=[word.pk, paradigm.pk, "edit"])

    def test_all_forms_changed(self, client, permissioned_user, multirow_paradigm):
        """Test the view can update a 3x2 paradigm where all forms are changed."""
        client.force_login(permissioned_user)
        word, paradigm, conjugations = multirow_paradigm
        url = self.get_edit_url(word, paradigm)
        response = client.get(url)
        formset = response.context["formset"]
        data = formset.management_form.initial
        # Change all conjugations
        for i, form in enumerate(formset.forms):
            data[f"form-{i}-conjugation"] = f"changed_{i}"
            data[f"form-{i}-id"] = form.instance.id if form.instance.id else ""
        data["form-TOTAL_FORMS"] = formset.total_form_count()
        data["form-INITIAL_FORMS"] = formset.initial_form_count()
        data["form-MIN_NUM_FORMS"] = 0
        data["form-MAX_NUM_FORMS"] = 1000
        post_response = client.post(url, data)
        assert post_response.status_code == 200
        # All conjugations should be changed
        for i, conj in enumerate(
            models.Conjugation.objects.filter(word=word, paradigm=paradigm).order_by(
                "id"
            )
        ):
            assert conj.conjugation == f"changed_{i}"

    def test_only_one_changed(self, client, permissioned_user, multirow_paradigm):
        """Test the view can update a 3x2 paradigm where 1 form is changed."""
        client.force_login(permissioned_user)
        word, paradigm, conjugations = multirow_paradigm
        url = self.get_edit_url(word, paradigm)
        response = client.get(url)
        formset = response.context["formset"]
        data = formset.management_form.initial
        # Change only the first conjugation
        for i, form in enumerate(formset.forms):
            if i == 0:
                data[f"form-{i}-conjugation"] = "only_changed"
            else:
                data[f"form-{i}-conjugation"] = form.instance.conjugation
            data[f"form-{i}-id"] = form.instance.id if form.instance.id else ""
        data["form-TOTAL_FORMS"] = formset.total_form_count()
        data["form-INITIAL_FORMS"] = formset.initial_form_count()
        data["form-MIN_NUM_FORMS"] = 0
        data["form-MAX_NUM_FORMS"] = 1000
        post_response = client.post(url, data)
        assert post_response.status_code == 200
        # Only the first conjugation should be changed
        for i, conj in enumerate(
            models.Conjugation.objects.filter(word=word, paradigm=paradigm).order_by(
                "id"
            )
        ):
            if i == 0:
                assert conj.conjugation == "only_changed"
            else:
                assert conj.conjugation == f"orig_{conj.row}_{conj.column}"

    def test_blank_forms_in_middle(self, client, permissioned_user, multirow_paradigm):
        """Test the view can update a 3x2 paradigm where there are blank forms."""
        client.force_login(permissioned_user)
        word, paradigm, conjugations = multirow_paradigm
        url = self.get_edit_url(word, paradigm)
        response = client.get(url)
        formset = response.context["formset"]
        data = formset.management_form.initial
        # Set the middle form blank
        for i, form in enumerate(formset.forms):
            if i == 2:
                data[f"form-{i}-conjugation"] = ""
            else:
                data[f"form-{i}-conjugation"] = form.instance.conjugation
            data[f"form-{i}-id"] = form.instance.id if form.instance.id else ""
        data["form-TOTAL_FORMS"] = formset.total_form_count()
        data["form-INITIAL_FORMS"] = formset.initial_form_count()
        data["form-MIN_NUM_FORMS"] = 0
        data["form-MAX_NUM_FORMS"] = 1000
        post_response = client.post(url, data)
        assert post_response.status_code == 200
        # The blank form should be blank, others unchanged
        for i, conj in enumerate(
            models.Conjugation.objects.filter(word=word, paradigm=paradigm).order_by(
                "id"
            )
        ):
            if i == 2:
                assert conj.conjugation == ""
            else:
                assert conj.conjugation == f"orig_{conj.row}_{conj.column}"

    # can't get the delte test to work
    def test_remove_conjugation(self, client, permissioned_user, multirow_paradigm):
        """Test the view can update a 3x2 paradigm, ensuring blank rows are deleted from db."""
        client.force_login(permissioned_user)
        word, paradigm, conjugations = multirow_paradigm
        initial_conjugation_number = models.Conjugation.objects.filter(
            word=word, paradigm=paradigm
        ).count()
        assert initial_conjugation_number == 6
        url = self.get_edit_url(word, paradigm)
        response = client.get(url)
        formset = response.context["formset"]
        data = formset.management_form.initial

        # Remove the last conjugation by omitting its id and values
        for i, form in enumerate(formset.forms):
            data[f"form-{i}-conjugation"] = "changed"
            data[f"form-{i}-id"] = form.instance.id if form.instance.id else ""
            if i == len(formset.forms) - 1:
                # overwrite the last form to submit blank.
                data[f"form-{i}-conjugation"] = form.instance.conjugation
        data["form-TOTAL_FORMS"] = formset.total_form_count()
        data["form-INITIAL_FORMS"] = formset.initial_form_count()
        data["form-MIN_NUM_FORMS"] = 0
        data["form-MAX_NUM_FORMS"] = 1000
        post_response = client.post(url, data)
        assert post_response.status_code == 200
        # The last conjugation should be deleted
        assert (
            models.Conjugation.objects.filter(word=word, paradigm=paradigm).count()
            == initial_conjugation_number - 1
        )

    def test_update_conjugation_invalid_tok_ples_chars(
        self, client, permissioned_user, multirow_paradigm, english_project
    ):
        """
        POST data with tok_ples violating the project's regex validator
        should re-render the form with validation errors and not save the entry.
        """
        client.force_login(permissioned_user)

        word, paradigm, conjugations = multirow_paradigm
        english_project.tok_ples_validator = "[a-z]+"
        english_project.save()
        url = self.get_edit_url(word, paradigm)
        response = client.get(url)
        formset = response.context["formset"]
        data = formset.management_form.initial

        # Remove the last conjugation by omitting its id and values
        for i, form in enumerate(formset.forms):
            data[f"form-{i}-conjugation"] = "changed"
            data[f"form-{i}-id"] = form.instance.id if form.instance.id else ""
            if i == len(formset.forms) - 1:
                # overwrite the last form to submit blank.
                data[f"form-{i}-conjugation"] = "changed 123"
        data["form-TOTAL_FORMS"] = formset.total_form_count()
        data["form-INITIAL_FORMS"] = formset.initial_form_count()
        data["form-MIN_NUM_FORMS"] = 0
        data["form-MAX_NUM_FORMS"] = 1000
        post_response = client.post(url, data)
        # form should be submitted with errors
        assert post_response.status_code == 200
        # The last conjugation should be deleted
        assert (
            "Conjugation &#x27;changed 123&#x27; contains unallowed characters."
            in post_response.content.decode()
        )
        assert (
            'name="form-5-conjugation" value="changed 123"'
            in post_response.content.decode()
        )

