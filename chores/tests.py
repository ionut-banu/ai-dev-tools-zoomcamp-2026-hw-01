from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from chores.models import Chore, CompletionLog, HouseholdMember


def make_chore(**overrides):
    defaults = dict(
        name="Dishes",
        kind=Chore.KIND_ONE_OFF,
        assignment_mode=Chore.ASSIGNMENT_MANUAL,
        next_due_date=date.today(),
    )
    defaults.update(overrides)
    return Chore(**defaults)


class ChoreValidationTests(TestCase):
    def test_valid_one_off_chore_passes_clean(self):
        member = HouseholdMember.objects.create(name="Alex")
        chore = make_chore(assignee=member)

        chore.full_clean()

    def test_valid_recurring_chore_passes_clean(self):
        member = HouseholdMember.objects.create(name="Alex")
        chore = make_chore(
            kind=Chore.KIND_RECURRING,
            interval_days=7,
            assignee=member,
        )

        chore.full_clean()

    def test_one_off_chore_rejects_interval_days(self):
        member = HouseholdMember.objects.create(name="Alex")
        chore = make_chore(assignee=member, interval_days=5)

        with self.assertRaises(ValidationError) as cm:
            chore.full_clean()
        self.assertIn("interval_days", cm.exception.message_dict)

    def test_recurring_chore_requires_interval_days(self):
        member = HouseholdMember.objects.create(name="Alex")
        chore = make_chore(kind=Chore.KIND_RECURRING, assignee=member)

        with self.assertRaises(ValidationError) as cm:
            chore.full_clean()
        self.assertIn("interval_days", cm.exception.message_dict)

    def test_manual_assignment_requires_assignee(self):
        chore = make_chore()

        with self.assertRaises(ValidationError) as cm:
            chore.full_clean()
        self.assertIn("assignee", cm.exception.message_dict)

    def test_auto_rotate_rejects_fewer_than_two_pool_members(self):
        member = HouseholdMember.objects.create(name="Alex")
        chore = make_chore(
            kind=Chore.KIND_RECURRING,
            interval_days=1,
            assignment_mode=Chore.ASSIGNMENT_AUTO_ROTATE,
        )
        chore.save()
        chore.rotation_pool.add(member)

        with self.assertRaises(ValidationError) as cm:
            chore.full_clean()
        self.assertIn("rotation_pool", cm.exception.message_dict)

    def test_auto_rotate_accepts_two_or_more_pool_members(self):
        member1 = HouseholdMember.objects.create(name="Alex")
        member2 = HouseholdMember.objects.create(name="Sam")
        chore = make_chore(
            kind=Chore.KIND_RECURRING,
            interval_days=1,
            assignment_mode=Chore.ASSIGNMENT_AUTO_ROTATE,
        )
        chore.save()
        chore.rotation_pool.add(member1, member2)

        chore.full_clean()


class CompletionLogTests(TestCase):
    def test_completion_log_can_be_created(self):
        member = HouseholdMember.objects.create(name="Alex")
        chore = make_chore(assignee=member)
        chore.save()
        due_date = date.today() - timedelta(days=1)

        log = CompletionLog.objects.create(
            chore=chore,
            completed_by=member,
            completed_at="2026-09-07T10:00:00Z",
            due_date_at_completion=due_date,
        )

        self.assertEqual(log.chore, chore)
        self.assertEqual(log.completed_by, member)
        self.assertEqual(log.due_date_at_completion, due_date)
