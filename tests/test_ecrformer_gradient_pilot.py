from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from experiments.ecrformer_gradient_pilot.gradient_loss import (
    add_gradient_term,
    gradient_preservation_loss,
)
import sys

PILOT_DIR = Path(__file__).resolve().parents[1] / "experiments" / "ecrformer_gradient_pilot"
if str(PILOT_DIR) not in sys.path:
    sys.path.insert(0, str(PILOT_DIR))

from evaluate_pilot import measure_patch
from train_ecrformer import (
    compose_training_loss,
    gaussian_window,
    load_epoch30_ema,
    resolve_experiment_dirs,
    validate_pilot_options,
)


def test_identical_prediction_has_zero_gradient_loss():
    target = torch.rand(2, 4, 16, 16)
    assert gradient_preservation_loss(target, target).item() == 0.0


def test_loss_increases_when_checkerboard_detail_is_removed():
    checker = (torch.arange(16)[:, None] + torch.arange(16)[None, :]) % 2
    target = checker.float().mul(0.2).add(0.2)[None, None].repeat(2, 4, 1, 1)
    blurred = torch.nn.functional.avg_pool2d(target, kernel_size=3, stride=1, padding=1)
    assert gradient_preservation_loss(blurred, target) > gradient_preservation_loss(target, target)


def test_each_of_four_bands_contributes():
    target = torch.zeros(1, 4, 8, 8)
    values = []
    for band in range(4):
        pred = target.clone()
        pred[:, band, :, 4:] = 1.0
        values.append(gradient_preservation_loss(pred, target))
    assert all(torch.isfinite(value) and value.item() > 0 for value in values)
    assert torch.allclose(torch.stack(values), torch.stack(values)[0].expand(4))


def test_loss_is_finite_and_backpropagates_on_available_devices():
    devices = [torch.device("cpu")]
    if torch.cuda.is_available():
        devices.append(torch.device("cuda"))
    for device in devices:
        pred = torch.rand(2, 4, 16, 16, device=device, requires_grad=True)
        target = torch.rand_like(pred)
        loss = gradient_preservation_loss(pred, target)
        assert loss.device.type == device.type
        assert torch.isfinite(loss)
        loss.backward()
        assert pred.grad is not None and torch.isfinite(pred.grad).all()


def test_invalid_channel_or_shape_is_rejected():
    with pytest.raises(ValueError, match="four optical bands"):
        gradient_preservation_loss(torch.rand(1, 3, 8, 8), torch.rand(1, 3, 8, 8))
    with pytest.raises(ValueError, match="same shape"):
        gradient_preservation_loss(torch.rand(1, 4, 8, 8), torch.rand(1, 4, 7, 8))
    if torch.cuda.is_available():
        with pytest.raises(ValueError, match="same device"):
            gradient_preservation_loss(
                torch.rand(1, 4, 8, 8, device="cpu"),
                torch.rand(1, 4, 8, 8, device="cuda"),
            )


def test_zero_weight_returns_existing_loss_exactly():
    existing = torch.tensor(0.123456, requires_grad=True)
    pred = torch.rand(1, 4, 8, 8)
    target = torch.rand_like(pred)
    combined, gradient = add_gradient_term(existing, pred, target, 0.0)
    assert combined is existing
    assert torch.equal(combined, existing)
    assert gradient.item() == 0.0


def test_nonzero_weight_adds_only_weighted_gradient_term():
    existing = torch.tensor(0.25)
    pred = torch.rand(1, 4, 8, 8)
    target = torch.rand_like(pred)
    combined, gradient = add_gradient_term(existing, pred, target, 0.1)
    assert torch.allclose(gradient, gradient_preservation_loss(pred, target))
    assert torch.allclose(combined, existing + 0.1 * gradient)


def test_fixed_cohort_does_not_include_held_out_scene():
    cohort = {
        "ROIs1970_fall_s2_119_p208",
        "ROIs1970_fall_s2_119_p236",
        "ROIs1970_fall_s2_119_p92",
        "ROIs1970_fall_s2_40_p268",
        "ROIs1970_fall_s2_65_p328",
        "ROIs1970_fall_s2_65_p124",
        "ROIs1970_fall_s2_119_p100",
        "ROIs1970_fall_s2_65_p336",
    }
    assert all("s2_139" not in sample for sample in cohort)


def test_load_epoch30_ema_uses_ema_state_and_refreshes_tracker(tmp_path):
    model = torch.nn.Linear(3, 2)
    model_ema = torch.nn.Linear(3, 2)
    expected = torch.nn.Linear(3, 2)
    raw = torch.nn.Linear(3, 2)
    with torch.no_grad():
        for parameter in expected.parameters():
            parameter.fill_(0.25)
        for parameter in raw.parameters():
            parameter.fill_(0.75)
    path = tmp_path / "epoch30.pth"
    torch.save({
        "epoch": 30,
        "ema_state_dict": expected.state_dict(),
        "model_state_dict": raw.state_dict(),
        "optimizer_state_dict": {"not": "loaded"},
        "scheduler_state_dict": {"not": "loaded"},
    }, path)

    checkpoint, digest = load_epoch30_ema(model, model_ema, path)

    assert checkpoint["epoch"] == 30
    assert len(digest) == 64
    assert all(torch.equal(model.state_dict()[key], expected.state_dict()[key]) for key in expected.state_dict())
    assert all(torch.equal(model_ema.state_dict()[key], expected.state_dict()[key]) for key in expected.state_dict())
    assert not all(torch.equal(model.state_dict()[key], raw.state_dict()[key]) for key in raw.state_dict())


def test_load_epoch30_ema_rejects_wrong_epoch_and_missing_ema(tmp_path):
    model = torch.nn.Linear(2, 2)
    tracker = torch.nn.Linear(2, 2)
    path = tmp_path / "wrong.pth"
    torch.save({"epoch": 29, "ema_state_dict": model.state_dict()}, path)
    with pytest.raises(ValueError, match="epoch-30"):
        load_epoch30_ema(model, tracker, path)
    torch.save({"epoch": 30, "model_state_dict": model.state_dict()}, path)
    with pytest.raises(ValueError, match="ema_state_dict"):
        load_epoch30_ema(model, tracker, path)


def test_ema_initialization_does_not_restore_optimizer_or_scheduler(tmp_path):
    model = torch.nn.Linear(2, 2)
    tracker = torch.nn.Linear(2, 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=3, eta_min=1e-5)
    expected_lr = optimizer.param_groups[0]["lr"]
    path = tmp_path / "epoch30.pth"
    torch.save({
        "epoch": 30,
        "ema_state_dict": tracker.state_dict(),
        "optimizer_state_dict": {"sentinel": 7},
        "scheduler_state_dict": {"sentinel": 9},
    }, path)

    load_epoch30_ema(model, tracker, path)

    assert optimizer.state == {}
    assert scheduler.last_epoch == 0
    assert optimizer.param_groups[0]["lr"] == expected_lr


def test_pilot_options_reject_resume_and_unsafe_weights():
    base = dict(lambda_gradient=0.1, init_from_ema="baseline.pth", experiment_dir="experiments/ecrformer_gradient_pilot", resume=False)
    with pytest.raises(ValueError, match="cannot be combined"):
        validate_pilot_options(SimpleNamespace(**{**base, "resume": True}))
    with pytest.raises(ValueError, match="finite and non-negative"):
        validate_pilot_options(SimpleNamespace(**{**base, "lambda_gradient": float("nan")}))
    with pytest.raises(ValueError, match="finite and non-negative"):
        validate_pilot_options(SimpleNamespace(**{**base, "lambda_gradient": -0.1}))


def test_positive_gradient_weight_requires_isolated_ema_init():
    with pytest.raises(ValueError, match="requires --init_from_ema and --experiment_dir"):
        validate_pilot_options(SimpleNamespace(lambda_gradient=0.1, init_from_ema=None, experiment_dir=None, resume=False))


def test_experiment_paths_are_fixed_and_refuse_existing_run_artifacts(tmp_path):
    root = tmp_path / "project"
    pilot = root / "experiments" / "ecrformer_gradient_pilot"
    ckpt_dir, output_dir = resolve_experiment_dirs("experiments/ecrformer_gradient_pilot", "pilot", root)
    assert ckpt_dir == str(pilot / "checkpoints" / "pilot")
    assert output_dir == str(pilot / "outputs" / "pilot")

    Path(output_dir).mkdir(parents=True)
    (Path(output_dir) / "history.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="Refusing to reuse"):
        resolve_experiment_dirs("experiments/ecrformer_gradient_pilot", "pilot", root)


def test_experiment_paths_reject_run_name_traversal(tmp_path):
    with pytest.raises(ValueError, match="run_name"):
        resolve_experiment_dirs("experiments/ecrformer_gradient_pilot", "../outside", tmp_path)


def test_compose_training_loss_zero_weight_preserves_existing_metrics_exactly():
    existing = torch.tensor(0.123456, requires_grad=True)
    existing_metrics = {
        "loss_total": existing.item(),
        "loss_main": 0.11,
        "loss_enc_aux": 0.22,
        "loss_dec_aux": 0.33,
    }
    pred = torch.rand(1, 4, 8, 8)
    target = torch.rand_like(pred)

    combined, metrics = compose_training_loss(existing, existing_metrics, pred, target, 0.0)

    assert combined is existing
    assert metrics["loss_total"] == existing_metrics["loss_total"]
    for key in ("loss_main", "loss_enc_aux", "loss_dec_aux"):
        assert metrics[key] == existing_metrics[key]
    assert metrics["loss_gradient"] == 0.0
    assert metrics["loss_gradient_weighted"] == 0.0


def test_compose_training_loss_adds_only_weighted_gradient_component():
    existing = torch.tensor(0.25, requires_grad=True)
    existing_metrics = {"loss_total": 0.25, "loss_main": 0.1, "loss_enc_aux": 0.2, "loss_dec_aux": 0.3}
    pred = torch.rand(1, 4, 8, 8)
    target = torch.rand_like(pred)

    combined, metrics = compose_training_loss(existing, existing_metrics, pred, target, 0.1)
    expected_gradient = gradient_preservation_loss(pred, target)

    assert torch.allclose(combined, existing + 0.1 * expected_gradient)
    assert metrics["loss_gradient"] == pytest.approx(expected_gradient.item())
    assert metrics["loss_gradient_weighted"] == pytest.approx(0.1 * expected_gradient.item())
    assert metrics["loss_total"] == pytest.approx(combined.item())
    assert metrics["loss_main"] == existing_metrics["loss_main"]
    assert metrics["loss_enc_aux"] == existing_metrics["loss_enc_aux"]
    assert metrics["loss_dec_aux"] == existing_metrics["loss_dec_aux"]


def test_patch_metrics_report_perfect_raw_reconstruction_and_gradient():
    axis = torch.arange(16, dtype=torch.float32)
    yy, xx = torch.meshgrid(axis, axis, indexing="ij")
    target = torch.stack([0.05 + 0.1 * band + 0.002 * xx + 0.003 * yy for band in range(4)])
    mask = torch.zeros(1, 16, 16)
    mask[:, :, 8:] = 1.0

    metrics = measure_patch(target, target, target, target, mask, gaussian_window())

    assert metrics["raw_psnr"] == pytest.approx(120.0)
    assert metrics["raw_mae"] == 0.0
    assert metrics["raw_ssim"] == pytest.approx(1.0)
    assert metrics["raw_gradient_l1"] == 0.0
    assert metrics["raw_gradient_energy_ratio"] == pytest.approx(1.0)
    assert metrics["raw_out_of_range_fraction"] == 0.0
    assert metrics["mask_coverage"] == pytest.approx(0.5)
    assert all(metrics[f"raw_{band}_bias"] == 0.0 for band in ("R", "G", "B", "NIR"))
