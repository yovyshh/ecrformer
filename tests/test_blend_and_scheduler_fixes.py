"""Tests for the approved Fix 1 (raw vs blended outputs) and Fix 2 (scheduler persistence),
plus read-only guards for Fix 3 (cache range) and the held-out split.

Lightweight: CPU only, tiny tensors, no training, no GPU, no writes to existing artifacts.
Run:  python -m pytest tests/test_blend_and_scheduler_fixes.py -v
"""
import os
import sys
import glob
import math
import numpy as np
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from models.ecrformer_adapted import ECRformerAdaptedModel      # noqa: E402
from train_ecrformer import validate                            # noqa: E402

CACHE_VAL = r"C:\Users\Windows 11 Pro\Videos\Projects\GAN\cache_fall_v3\val"


# --------------------------------------------------------------------------- Fix 1
def test_blend_equation_is_identity_in_clear_and_raw_in_cloudy():
    """out = (1-m)*cloudy + m*pred_direct : strict identity where m==0, raw where m==1."""
    torch.manual_seed(0)
    model = ECRformerAdaptedModel(features_start=32, num_blocks=[2, 2, 1, 1], num_refine=0,
                                  bottle_neck='tsa', cbam='1ca2+1sa2', mask_blend=True,
                                  head_init='mean_prior').eval()
    s2c = torch.rand(1, 4, 128, 128)
    s1 = torch.rand(1, 2, 128, 128)
    m = torch.zeros(1, 1, 128, 128)
    m[:, :, :64] = 1.0                                   # deterministic split
    with torch.no_grad():
        out, raw, _ = model(s2c, s1, m)

    assert out.shape == raw.shape == (1, 4, 128, 128)
    # equation
    assert torch.allclose(out, (1 - m) * s2c + m * raw, atol=1e-6)
    # clear region (m==0): output is EXACTLY the cloudy input -> identical to the no-removal baseline
    assert torch.equal(out[:, :, 64:], s2c[:, :, 64:])
    # cloudy region (m==1): output is exactly the raw network output
    assert torch.equal(out[:, :, :64], raw[:, :, :64])
    # and the raw output is NOT a copy of the input there
    assert not torch.allclose(raw[:, :, :64], s2c[:, :, :64])


class _FakeModel(torch.nn.Module):
    """Returns (blend, raw) where raw is perfect and blend is deliberately bad."""
    def __init__(self, target_bad_offset=0.5):
        super().__init__()
        self.off = target_bad_offset

    def forward(self, s2_c, s1, mask):
        raw = torch.full_like(s2_c, torch.nan)           # replaced by loader-matching value below
        return s2_c + self.off, raw, None


def _fake_loader(target):
    s2c = torch.rand(2, 4, 32, 32)
    yield s2c, torch.zeros(2, 2, 32, 32), target, torch.tensor([0.4, 0.8]), (torch.rand(2, 1, 32, 32) > 0.3).float()


def test_validate_scores_raw_and_blend_separately():
    """validate() must compute raw_* from pred_direct and blend_* from the blended tensor,
    and the legacy unsuffixed keys must follow `select`."""
    tgt = torch.rand(2, 4, 32, 32)

    class M(torch.nn.Module):
        def forward(self, s2_c, s1, mask):
            return tgt.clone(), tgt.clone() + 0.25, None      # blend perfect, raw bad

    res = validate(_fake_loader(tgt), M(), device='cpu', max_batches=None, precision='fp32', select='raw')
    a = res['all']
    for k in ('raw_psnr', 'blend_psnr', 'raw_ssim', 'blend_ssim', 'raw_l1', 'blend_l1',
              'raw_pearson', 'blend_pearson', 'raw_ndvi_mae', 'blend_ndvi_mae'):
        assert k in a, f"missing {k}"
    assert a['raw_psnr'] < a['blend_psnr']                    # raw is deliberately worse here
    assert a['raw_l1'] > a['blend_l1']
    # legacy aliases follow `select`
    assert a['psnr'] == a['raw_psnr'] and a['l1'] == a['raw_l1'] and a['select'] == 'raw'

    res2 = validate(_fake_loader(tgt), M(), device='cpu', max_batches=None, precision='fp32', select='blend')
    b = res2['all']
    assert b['psnr'] == b['blend_psnr'] and b['l1'] == b['blend_l1'] and b['select'] == 'blend'
    # the per-variant values do not depend on `select`
    assert b['raw_psnr'] == a['raw_psnr'] and b['blend_psnr'] == a['blend_psnr']


def test_validate_rejects_unknown_select():
    try:
        validate(_fake_loader(torch.rand(2, 4, 32, 32)), _FakeModel(), device='cpu', select='nope')
    except ValueError:
        return
    raise AssertionError("validate() should reject an unknown select value")


# --------------------------------------------------------------------------- Fix 2
def _cosine(base, min_lr, T, n):
    return min_lr + (base - min_lr) * (1.0 + math.cos(math.pi * n / T)) / 2.0


def test_fallback_formula_matches_real_scheduler():
    """The explicit LR formula used for legacy checkpoints must equal the scheduler's own LR."""
    base, mn, T = 4e-4, 1e-5, 50
    for n in (0, 1, 15, 29, 30, 31, 32, 40, 49):
        p = torch.nn.Parameter(torch.zeros(1))
        o = optim.Adam([p], lr=base)
        s = CosineAnnealingLR(o, T_max=T, eta_min=mn)
        for _ in range(n):
            s.step()
        assert abs(o.param_groups[0]['lr'] - _cosine(base, mn, T, n)) < 1e-12, f"n={n}"


def test_scheduler_state_roundtrip_preserves_position_and_does_not_touch_lr():
    base, mn, T = 4e-4, 1e-5, 50
    p = torch.nn.Parameter(torch.zeros(1))
    o = optim.Adam([p], lr=base)
    s = CosineAnnealingLR(o, T_max=T, eta_min=mn)
    for _ in range(32):
        s.step()
    lr_at_ckpt = o.param_groups[0]['lr']
    sd, od = s.state_dict(), o.state_dict()

    o2 = optim.Adam([p], lr=base)                 # fresh, as on resume
    s2 = CosineAnnealingLR(o2, T_max=T, eta_min=mn)
    o2.load_state_dict(od)                        # restore decayed LR first (as in main())
    s2.load_state_dict(sd)                        # then restore scheduler position
    assert s2.last_epoch == s.last_epoch == 32
    assert abs(o2.param_groups[0]['lr'] - lr_at_ckpt) < 1e-15     # untouched by load_state_dict


def test_old_replay_behaviour_would_have_drifted():
    """Regression guard for the ORIGINAL bug: restoring the optimizer LR and then replaying
    `start_epoch` steps on a FRESH scheduler overwrites it with an off-schedule value."""
    base, mn, T = 4e-4, 1e-5, 50
    p = torch.nn.Parameter(torch.zeros(1))
    o = optim.Adam([p], lr=base)
    s = CosineAnnealingLR(o, T_max=T, eta_min=mn)
    for _ in range(32):
        s.step()
    lr_at_ckpt = o.param_groups[0]['lr']

    o2 = optim.Adam([p], lr=base)
    o2.load_state_dict(o.state_dict())            # lr = lr_at_ckpt  (correct)
    s2 = CosineAnnealingLR(o2, T_max=T, eta_min=mn)   # fresh -> last_epoch = 0
    for _ in range(31):                           # the OLD replay loop
        s2.step()
    assert abs(o2.param_groups[0]['lr'] - lr_at_ckpt) > 1e-6, "replay should NOT reproduce the checkpoint LR"


# --------------------------------------------------------------------------- Fix 3 / safety
def test_val_split_is_readable_and_excludes_held_out_scene():
    files = sorted(glob.glob(os.path.join(CACHE_VAL, "*.npz")))
    assert len(files) == 1115, f"expected 1115 val patches, found {len(files)}"
    assert not any("s2_139" in os.path.basename(f) for f in files), "held-out scene s2_139 leaked into val"


def test_cache_reflectance_range_is_documented_not_silently_changed():
    """Fix 3: the cache is NOT clipped. Guard the documented fact that inputs exceed 1.0."""
    checked = 0
    any_over = 0
    for f in sorted(glob.glob(os.path.join(CACHE_VAL, "*.npz")))[:200]:
        d = np.load(f)
        c = d["s2_cloudy"].astype(np.float32)
        assert c.min() >= 0.0, f"negative reflectance in {f}"
        checked += 1
        if c.max() > 1.0:
            any_over += 1
    assert checked == 200
    # documented: ~9.8% of val patches contain at least one pixel > 1.0
    assert any_over > 0, "expected some patches to exceed 1.0 (cache is intentionally unclipped)"
