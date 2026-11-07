"""Deterministic miniature reference test: uninterrupted cosine schedule vs save/resume at epoch 32.

Settles the EPOCH-INDEX CONVENTION and verifies the LR actually used by the first optimizer
update after resuming, the scheduler state, and the subsequent LR sequence.

Convention under test (matches train_ecrformer.main()):
    scheduler = CosineAnnealingLR(...)             # last_epoch = 0, lr = base
    for epoch in range(start_epoch, epochs):       # LR for THIS epoch read at the top
        current_lr = optimizer.param_groups[0]['lr']
        <optimizer updates happen here>
        scheduler.step()                           # advanced at the END of the epoch

  => the LR used for 0-based epoch k is closed_form(k), and history.json[k] == closed_form(k).
  => on resume with ckpt['epoch'] == E, the first resumed epoch is 0-based E and its LR
     must be closed_form(E) -- NOT closed_form(E+1).

Deterministic, CPU, no training, no data.
"""
import os
import sys
import math
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

BASE, MIN_LR, T_MAX = 4e-4, 1e-5, 50
E_CKPT = 32                     # ckpt['epoch'] -> 32 completed epochs (matches latest_model.pth)


def closed_form(n):
    """The schedule's own LR at step count n, and the formula used by the legacy fallback."""
    return MIN_LR + (BASE - MIN_LR) * (1.0 + math.cos(math.pi * n / T_MAX)) / 2.0


def _fresh():
    p = torch.nn.Parameter(torch.zeros(1))
    o = optim.Adam([p], lr=BASE)
    s = CosineAnnealingLR(o, T_max=T_MAX, eta_min=MIN_LR)
    return o, s


def run_reference(n_epochs=T_MAX):
    """Uninterrupted run. Returns the LR used by the optimizer updates of each 0-based epoch."""
    o, s = _fresh()
    lrs = []
    for _e in range(n_epochs):
        lrs.append(o.param_groups[0]['lr'])      # LR this epoch's updates will use
        o.step()                                 # a real update; does not alter param_groups['lr']
        s.step()
    return lrs


# --------------------------------------------------------------------- convention
def test_reference_schedule_is_closed_form_of_epoch_index():
    lrs = run_reference()
    for k, lr in enumerate(lrs):
        assert abs(lr - closed_form(k)) < 1e-15, f"epoch {k}: {lr} != {closed_form(k)}"


def test_epoch_index_convention_start_epoch_not_plus_one():
    """The first resumed epoch's LR is closed_form(E), NOT closed_form(E+1)."""
    assert abs(closed_form(E_CKPT) - 1.2197302e-04) < 1e-9       # epoch displayed as 33
    assert abs(closed_form(E_CKPT + 1) - 1.1105824e-04) < 1e-9   # epoch displayed as 34
    assert closed_form(E_CKPT) > closed_form(E_CKPT + 1)         # schedule must still decay


# --------------------------------------------------------------------- save / resume
def test_save_resume_at_epoch_32_reproduces_uninterrupted_schedule():
    ref = run_reference()

    # ---- process 1: train E_CKPT epochs, then save (scheduler.step() happens before the save)
    o1, s1 = _fresh()
    for _e in range(E_CKPT):
        o1.step()
        s1.step()
    ck_opt, ck_sched = o1.state_dict(), s1.state_dict()
    assert s1.last_epoch == E_CKPT, "scheduler position must equal the completed-epoch count"
    assert abs(o1.param_groups[0]['lr'] - closed_form(E_CKPT)) < 1e-15, \
        "a CORRECT checkpoint stores the on-schedule LR for the next epoch"

    # ---- process 2: resume exactly as train_ecrformer.main() does
    o2, s2 = _fresh()
    o2.load_state_dict(ck_opt)          # restores the decayed LR
    s2.load_state_dict(ck_sched)        # restores the position (NO replay loop)
    assert s2.last_epoch == E_CKPT
    assert abs(o2.param_groups[0]['lr'] - closed_form(E_CKPT)) < 1e-15

    resumed = []
    for _e in range(E_CKPT, T_MAX):
        resumed.append(o2.param_groups[0]['lr'])
        o2.step()
        s2.step()

    assert len(resumed) == T_MAX - E_CKPT
    assert abs(resumed[0] - closed_form(E_CKPT)) < 1e-15
    for i, lr in enumerate(resumed):
        assert abs(lr - ref[E_CKPT + i]) < 1e-15, f"resumed epoch {E_CKPT+i} diverged from reference"
    assert abs(resumed[0] - 1.2197302e-04) < 1e-9        # the exact first-update LR


def test_legacy_fallback_with_force_lr_reproduces_uninterrupted_schedule():
    """No scheduler state -> explicit formula + last_epoch = start_epoch, as main() does."""
    ref = run_reference()
    o, s = _fresh()
    # the legacy checkpoint's stored optimizer LR is WRONG (off-schedule), as in latest_model.pth
    for g in o.param_groups:
        g['lr'] = 2.222228249254485e-05

    # ---- resume path, legacy branch with --resume_force_lr
    start_epoch = E_CKPT
    intended_lr = closed_form(start_epoch)      # the formula in main()
    s.last_epoch = start_epoch
    for g in o.param_groups:
        g['lr'] = intended_lr

    resumed = []
    for _e in range(start_epoch, T_MAX):
        resumed.append(o.param_groups[0]['lr'])
        o.step()
        s.step()

    assert abs(resumed[0] - ref[start_epoch]) < 1e-15
    for i, lr in enumerate(resumed):
        assert abs(lr - ref[start_epoch + i]) < 1e-15, f"legacy+force diverged at {start_epoch+i}"


def test_legacy_fallback_without_force_keeps_off_schedule_lr():
    """Without the flag the LR is NOT rewritten - it stays as saved (documented, not silent)."""
    o, s = _fresh()
    saved = 2.222228249254485e-05
    for g in o.param_groups:
        g['lr'] = saved
    s.last_epoch = E_CKPT
    # nothing forces the LR
    assert abs(o.param_groups[0]['lr'] - saved) < 1e-18
    # and it is measurably off-schedule
    assert abs(saved - closed_form(E_CKPT)) / closed_form(E_CKPT) > 0.8


# --------------------------------------------------------------------- wiring guards
def test_future_checkpoints_will_carry_and_restore_scheduler_state():
    src = open(os.path.join(REPO, "train_ecrformer.py"), encoding="utf-8").read()
    assert src.count("'scheduler_state_dict': scheduler.state_dict()") >= 2, \
        "both torch.save calls must write scheduler_state_dict"
    assert "scheduler.load_state_dict(ckpt['scheduler_state_dict'])" in src, \
        "resume must restore scheduler state when present"
    assert "for _ in range(start_epoch):" not in src, "the old replay loop must be gone"
